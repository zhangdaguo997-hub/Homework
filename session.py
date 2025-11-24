from roles import Analyst, Coder, Tester
from utils import find_method_name
import time
from utils import code_truncate


class Session(object):
    def __init__(self, TEAM, ANALYST, PYTHON_DEVELOPER, TESTER, requirement, model='deepseek-chat', majority=1, max_tokens=512,
                                temperature=0.0, top_p=0.95, max_round=4, before_func=''):

        self.session_history = {}
        self.max_round = max_round
        self.before_func = before_func
        self.requirement = requirement
        self.analyst = Analyst(TEAM, ANALYST, requirement, model, majority, max_tokens, temperature, top_p)
        self.coder = Coder(TEAM, PYTHON_DEVELOPER, requirement, model, majority, max_tokens, temperature, top_p)
        self.tester = Tester(TEAM, TESTER, requirement, model, majority, max_tokens, temperature, top_p)
    
    def run_session(self):
        """
        运行一个完整的代码生成与测试会话
        返回最终代码和会话历史记录
        """
        # 分析师分析需求并生成初始计划
        plan = self.analyst.analyze()
        report = plan
        is_init = True  # 标记是否为初始轮次
        self.session_history["plan"] = plan  # 保存计划到会话历史
        code = ""  # 初始化代码变量

        # 开始多轮迭代，最多进行max_round轮
        for i in range(self.max_round):

            # 程序员根据报告生成初始代码（首轮）或修复代码（后续轮次）
            naivecode = self.coder.implement(report, is_init)
            # 从生成的代码中提取方法名
            method_name = find_method_name(naivecode)
            if method_name:
                code = naivecode  # 如果找到方法名，使用生成的代码
                
            # 检查生成的代码是否为空
            if code.strip() == "":
                if i == 0:
                    code = "error"  # 首轮生成空代码则标记为错误
                else:
                    # 非首轮则使用上一轮的代码
                    code = self.session_history['Round_{}'.format(i-1)]["code"]
                break  # 退出循环
            
            # 如果是最后一轮，保存代码并退出循环
            if i == self.max_round-1:
                self.session_history['Round_{}'.format(i)] = {"code": code}
                break
            
            # 测试生成的代码
            tests = self.tester.test(code)
            # 截断测试报告
            test_report = code_truncate(tests)
            # 不安全执行代码进行测试验证
            answer_report = unsafe_execute(self.before_func+code+'\n'+test_report+'\n'+f'check({method_name})', '')
            # 生成测试报告
            report = f'The compilation output of the preceding code is: {answer_report}'

            is_init = False  # 标记为非初始轮次
            # 保存当前轮次的代码和报告到历史记录
            self.session_history['Round_{}'.format(i)] = {"code": code, "report": report}

            # 检查是否出现错误情况
            if (plan == "error") or (code == "error") or (report == "error"):
                code = "error"
                break  # 出现错误则退出循环
            
            # 如果测试通过，退出循环
            if answer_report == "Code Test Passed.":
                break

        # 清空所有接口的历史记录
        self.analyst.itf.clear_history()
        self.coder.itf.clear_history()
        self.tester.itf.clear_history()

        # 返回最终代码和完整的会话历史
        return code, self.session_history

    def run_analyst_coder(self):
        plan = self.analyst.analyze()
        is_init=True
        self.session_history["plan"] = plan
        code = self.coder.implement(plan, is_init)

        if (plan == "error") or (code == "error"):
            code = "error"

        self.analyst.itf.clear_history()
        self.coder.itf.clear_history()
        self.tester.itf.clear_history()

        return code, self.session_history


    def run_coder_tester(self):
        report = ""
        is_init=True
        code = ""
        
        for i in range(self.max_round):

            naivecode = self.coder.implement(report, is_init)
            if find_method_name(naivecode):
                code = naivecode

            if code.strip() == "":
                if i == 0:
                    code = self.coder.implement(report, is_init=True)
                else:
                    code = self.session_history['Round_{}'.format(i-1)]["code"]
                break
            
            if i == self.max_round-1:
                self.session_history['Round_{}'.format(i)] = {"code": code}
                break
            tests = self.tester.test(code)
            test_report = code_truncate(tests)
            answer_report = unsafe_execute(self.before_func+code+'\n'+test_report+'\n'+f'check({method_name})', '')
            report = f'The compilation output of the preceding code is: {answer_report}'

            is_init = False
            self.session_history['Round_{}'.format(i)] = {"code": code, "report": report}

            if (code == "error") or (report == "error"):
                code = "error"
                break
            
            if report == "Code Test Passed.":
                break

        self.analyst.itf.clear_history()
        self.coder.itf.clear_history()
        self.tester.itf.clear_history()

        return code, self.session_history

    def run_coder_only(self):
        plan = ""
        code = self.coder.implement(plan, is_init=True)
        self.coder.itf.clear_history()
        return code, self.session_history


import contextlib
import faulthandler
import io
import os
import platform
import signal
import tempfile 

def unsafe_execute(code, report):

        with create_tempdir():

            # These system calls are needed when cleaning up tempdir.
            import os
            import shutil
            rmtree = shutil.rmtree
            rmdir = os.rmdir
            chdir = os.chdir 

            # Disable functionalities that can make destructive changes to the test.
            reliability_guard()

            # Construct the check program and run it.
            check_program = (
                code + report
            )

            try:
                exec_globals = {}
                with swallow_io():
                    timeout = 10
                    with time_limit(timeout):
                        exec(check_program, exec_globals)
                result = "Code Test Passed."
            except AssertionError as e:
                result = f"failed with AssertionError. {e}"
            except TimeoutException:
                result = "timed out"
            except BaseException as e:
                result = f"{e}"


            # Needed for cleaning up.
            shutil.rmtree = rmtree
            os.rmdir = rmdir
            os.chdir = chdir
            return result


def reliability_guard(maximum_memory_bytes = None):
    """
    This disables various destructive functions and prevents the generated code
    from interfering with the test (e.g. fork bomb, killing other processes,
    removing filesystem files, etc.)

    WARNING
    This function is NOT a security sandbox. Untrusted code, including, model-
    generated code, should not be blindly executed outside of one. See the 
    Codex paper for more information about OpenAI's code sandbox, and proceed
    with caution.
    """

    if maximum_memory_bytes is not None:
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (maximum_memory_bytes, maximum_memory_bytes))
        resource.setrlimit(resource.RLIMIT_DATA, (maximum_memory_bytes, maximum_memory_bytes))
        if not platform.uname().system == 'Darwin':
            resource.setrlimit(resource.RLIMIT_STACK, (maximum_memory_bytes, maximum_memory_bytes))

    faulthandler.disable()

    import builtins
    builtins.exit = None
    builtins.quit = None

    import os
    os.environ['OMP_NUM_THREADS'] = '1'

    os.rmdir = None
    os.chdir = None

    import shutil
    shutil.rmtree = None
    shutil.move = None
    shutil.chown = None

    import subprocess
    subprocess.Popen = None  # type: ignore

    __builtins__['help'] = None

    import sys
    sys.modules['ipdb'] = None
    sys.modules['joblib'] = None
    sys.modules['resource'] = None
    sys.modules['psutil'] = None
    sys.modules['tkinter'] = None
    
@contextlib.contextmanager
def time_limit(seconds: float):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")
    signal.setitimer(signal.ITIMER_REAL, seconds)
    signal.signal(signal.SIGALRM, signal_handler)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


@contextlib.contextmanager
def swallow_io():
    stream = WriteOnlyStringIO()
    with contextlib.redirect_stdout(stream):
        with contextlib.redirect_stderr(stream):
            with redirect_stdin(stream):
                yield


@contextlib.contextmanager
def create_tempdir():
    with tempfile.TemporaryDirectory() as dirname:
        with chdir(dirname):
            yield dirname
            
class TimeoutException(Exception):
    pass


class WriteOnlyStringIO(io.StringIO):
    """ StringIO that throws an exception when it's read from """

    def read(self, *args, **kwargs):
        raise IOError

    def readline(self, *args, **kwargs):
        raise IOError

    def readlines(self, *args, **kwargs):
        raise IOError

    def readable(self, *args, **kwargs):
        """ Returns True if the IO object can be read. """
        return False


class redirect_stdin(contextlib._RedirectStream):  # type: ignore
    _stream = 'stdin'


@contextlib.contextmanager
def chdir(root):
    if root == ".":
        yield
        return
    cwd = os.getcwd()
    os.chdir(root)
    try:
        yield
    except BaseException as exc:
        raise exc
    finally:
        os.chdir(cwd)