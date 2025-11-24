# correct_evaluate.py
import json
import tempfile
import subprocess
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

def extract_function_name(completion):
    """从生成的代码中提取函数名"""
    match = re.search(r'def\s+(\w+)', completion)
    return match.group(1) if match else None

def correct_check_humaneval_task(task_data, timeout=10):
    """
    正确检查HumanEval任务：确保测试用例真正被执行
    """
    task_id = task_data["task_id"]
    prompt = task_data.get('prompt', '')
    completion = task_data.get('completion', '')
    test_cases = task_data.get('test', '')
    
    if not completion or completion.strip() == "error":
        return {
            "task_id": task_id,
            "passed": False,
            "reason": "empty_or_error"
        }
    
    # 提取函数名
    function_name = extract_function_name(completion)
    if not function_name:
        return {
            "task_id": task_id,
            "passed": False,
            "reason": "no_function_found"
        }
    
    # 构建完整程序：prompt + completion + test_cases + 调用check函数
    full_program = prompt + completion + "\n\n" + test_cases + f"\n\n# 执行测试\ncheck({function_name})"
    
    # 保存到临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(full_program)
        temp_file = f.name
    
    try:
        result = subprocess.run(
            ['python', temp_file],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        # 严格的通过条件：返回码为0且没有断言错误
        passed = (
            result.returncode == 0 and 
            "AssertionError" not in result.stderr and
            "Traceback" not in result.stderr
        )
        
        return {
            "task_id": task_id,
            "passed": passed,
            "function_name": function_name,
            "returncode": result.returncode,
            "stdout": result.stdout[:200] if result.stdout else "",
            "stderr": result.stderr[:200] if result.stderr else "",
            "has_assertion_error": "AssertionError" in result.stderr,
            "has_traceback": "Traceback" in result.stderr
        }
        
    except subprocess.TimeoutExpired:
        return {
            "task_id": task_id,
            "passed": False,
            "reason": "timeout"
        }
    except Exception as e:
        return {
            "task_id": task_id,
            "passed": False,
            "reason": f"exception: {str(e)}"
        }
    finally:
        try:
            os.unlink(temp_file)
        except:
            pass

def correct_evaluate():
    """正确评估所有任务"""
    
    with open('humaneval_output.jsonl', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    samples = [json.loads(line) for line in lines]
    print(f"📊 正确评估 {len(samples)} 个任务")
    print("🔄 这次会真正执行测试用例...")
    
    results = []
    passed_count = 0
    
    # 使用线程池并行处理
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_task = {executor.submit(correct_check_humaneval_task, sample): sample for sample in samples}
        
        completed = 0
        for future in as_completed(future_to_task):
            result = future.result()
            results.append(result)
            
            if result["passed"]:
                passed_count += 1
                print(f"✅ {completed+1:3d}/{len(samples)}: {result['task_id']} - 通过")
            else:
                reason = result.get('reason', '')
                if result.get('has_assertion_error'):
                    reason = "断言失败"
                elif result.get('has_traceback'):
                    reason = "运行时错误"
                print(f"❌ {completed+1:3d}/{len(samples)}: {result['task_id']} - 失败 ({reason})")
            
            completed += 1
    
    pass_rate = passed_count / len(samples) * 100
    
    print(f"\n🎯 正确评估结果:")
    print(f"  总任务数: {len(samples)}")
    print(f"  通过数: {passed_count}")
    print(f"  Pass@1: {pass_rate:.2f}%")
    
    # 详细统计
    reasons = {}
    for result in results:
        reason = result.get('reason', 'test_failed')
        if result['passed']:
            reason = 'passed'
        elif result.get('has_assertion_error'):
            reason = 'assertion_error'
        elif result.get('has_traceback'):
            reason = 'runtime_error'
        reasons[reason] = reasons.get(reason, 0) + 1
    
    print(f"\n📊 详细统计:")
    for reason, count in reasons.items():
        print(f"  {reason}: {count}")
    
    # 保存详细结果
    with open('correct_evaluation_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # 保存汇总统计
    summary = {
        "total_tasks": len(samples),
        "passed_tasks": passed_count,
        "pass_rate": pass_rate,
        "failure_breakdown": reasons,
        "model": "deepseek-chat",
        "evaluation_method": "correct_with_test_execution"
    }
    
    with open('correct_evaluation_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 详细结果已保存到: correct_evaluation_results.json")
    print(f"📋 汇总统计已保存到: correct_evaluation_summary.json")
    
    return pass_rate

if __name__ == "__main__":
    correct_evaluate()