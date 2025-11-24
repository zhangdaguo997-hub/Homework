from roles.analyst import Analyst
from roles.coder import Coder
from roles.tester import Tester
from roles.project_architect import ProjectArchitect
from roles.project_developer import ProjectDeveloper
from roles.project_tester import ProjectTester
from roles.ui_designer import UIDesigner
from utils import find_method_name, construct_system_message
from tools import global_tool_orchestrator, CodeAnalyzer, FileManager, QualityChecker, APIIntegrationTool, AutomatedTester
import time
import os
import json
import re


class ProjectSession(object):
    def __init__(self, team_description, architect_description, developer_description, 
                 tester_description, ui_designer_description, requirement, project_type='web_visualization',
                 model='deepseek-chat', majority=1, max_tokens=1024,
                 temperature=0.2, top_p=0.95, max_round=3, output_dir='generated_project'):
        # 初始化 ProjectSession
        # 参数说明（简要）:
        # - team_description: 项目团队描述（字符串或结构化描述）
        # - architect_description/developer_description/...: 各角色的描述或配置
        # - requirement: 项目需求描述（字符串）
        # - project_type: 项目类型（如 web_visualization）
        # - model: 使用的模型名称
        # - majority: 多样性/多数判断相关参数
        # - max_tokens: 用于每次调用的最大 token 数（会根据回合调整）
        # - temperature/top_p: 模型采样参数
        # - max_round: 多轮开发的最大轮数
        # - output_dir: 生成文件输出目录
        self.session_history = {}
        self.max_round = max_round
        self.requirement = requirement
        self.project_type = project_type
        self.output_dir = output_dir
        self.project_files = {}
        
        # Intelligently adjust max_tokens to avoid context length issues
        self.base_max_tokens = max_tokens
        self.current_max_tokens = max_tokens
        self.model = model
        
        # Dynamically adjust tokens based on model and rounds
        model_limits = {
            'deepseek-chat': 16385,
            'gpt-4': 16385,
            'deepseek-chat': 32768,  # DeepSeek有更大的上下文窗口
        }
        self.model_limit = model_limits.get(model, 16385)
        
        # Initial token allocation: reserve space for multi-round iteration
        if max_round > 1:
            # Use smaller tokens for multi-round iteration, reserve space for history
            adjusted_max_tokens = min(max_tokens, self.model_limit // (max_round + 1))
        else:
            adjusted_max_tokens = max_tokens
        
        print(f"🔧 Token management: Model={model}, Limit={self.model_limit}, Base={max_tokens}, Adjusted={adjusted_max_tokens}")
        
        # Initialize tools
        self.tool_orchestrator = global_tool_orchestrator  # 工具编排器：协调和管理所有工具的执行流程
        self.code_analyzer = CodeAnalyzer()  # 代码分析器：分析和检查生成的代码质量
        self.file_manager = FileManager()  # 文件管理器：处理项目文件的创建、保存和组织
        self.quality_checker = QualityChecker()  # 质量检查器：确保代码符合质量标准和最佳实践
        self.api_tool = APIIntegrationTool()  # API集成工具：处理外部API调用和第三方服务集成
        self.automated_tester = AutomatedTester()  # 自动化测试器：执行自动化测试和验证代码功能
        
        # Initialize project roles with adjusted tokens
        self.architect = ProjectArchitect(team_description, architect_description, requirement, 
                                        project_type, model, majority, adjusted_max_tokens, temperature, top_p)
        self.developer = ProjectDeveloper(team_description, developer_description, requirement,
                                        project_type, model, majority, adjusted_max_tokens, temperature, top_p)
        self.tester = ProjectTester(team_description, tester_description, requirement,
                                  project_type, model, majority, adjusted_max_tokens, temperature, top_p)
        self.ui_designer = UIDesigner(team_description, ui_designer_description, requirement,
                                    project_type, model, majority, adjusted_max_tokens, temperature, top_p)
    
    def _adjust_tokens_for_round(self, round_num):
        """Dynamically adjust token allocation based on round number"""
        # 根据回合动态调整 token 分配，目的是为会话历史保留足够的上下文窗口
        # 当前实现中 reduction_factor 保持为 1.0（可按需启用逐轮下降策略）
        reduction_factor = 1.0  # 如需每轮减少，可设置为 1.0 - (round_num * 0.1)
        # new_max_tokens 保证不会低于最小值 512，以避免太少的生成空间
        new_max_tokens = max(int(self.base_max_tokens * reduction_factor), 512)  # Minimum 512 tokens
        
        if new_max_tokens != self.current_max_tokens:
            print(f"🔄 Round {round_num + 1}: Adjusting max_tokens from {self.current_max_tokens} to {new_max_tokens}")
            self.current_max_tokens = new_max_tokens
            
            # Update token settings for all roles
            for role in [self.architect, self.developer, self.tester, self.ui_designer]:
                if hasattr(role, 'max_tokens'):
                    role.max_tokens = new_max_tokens
        
        return new_max_tokens
    
    
    def run_project_session(self):
        """修复版本 - 运行完整的项目生成会话，确保信息正确传递"""
        
        print("🔧 阶段 0: 初始化资源...")
        # 根据项目类型获取外部资源
        if self.project_type == 'web_visualization':
            external_resources = self.api_tool.execute(
                "fetch_cdn_libraries", 
                libraries=["chart.js", "d3.js", "bootstrap", "jquery"]
            )
            self.session_history["external_resources"] = external_resources
            print(f"✅ 已获取外部资源: {len(external_resources.get('libraries', []))} 个库")
        
        # 阶段 1: 规划和架构设计
        print("🏗️ 阶段 1: 创建规划和架构设计...")
        architecture_plan = self.architect.design_architecture()
        self.session_history["architecture"] = architecture_plan
        
        if architecture_plan == "error":
            raise RuntimeError("架构设计失败")
        
        print(f"✅ 架构设计完成，长度: {len(architecture_plan)} 字符")
        
        # 阶段 2: UI设计（适用于Web项目）
        ui_design = None
        if self.project_type in ['web_visualization', 'desktop_app']:
            print("🎨 阶段 2: 创建UI设计...")
            ui_design = self.ui_designer.design_ui(architecture_plan)
            self.session_history["ui_design"] = ui_design
            
            print(f"✅ UI设计完成，长度: {len(ui_design) if ui_design != 'error' else 'ERROR'} 字符")
        
        # 阶段 3: 开发，确保正确传递上下文
        print("⚡ 阶段 3: 使用完整上下文实施项目...")
        
        # 确保开发者有完整的上下文信息
        print(f"🔍 开发者历史消息长度: {len(self.developer.history_message)}")
        
        # 手动将架构和UI设计信息添加到开发者的上下文中
        development_context = f"""
        项目需求: {self.requirement}
        项目类型: {self.project_type}
        架构设计: {architecture_plan}
        {f"UI设计: {ui_design}" if ui_design and ui_design != "error" else ""}
        """
        
        # 清除开发者可能存在的旧消息（除了系统消息）
        if hasattr(self.developer, 'history_message') and len(self.developer.history_message) > 1:
            # 保留系统消息，清除其他
            system_message = self.developer.history_message[0]
            self.developer.history_message = [system_message]
            print("🧹 已清除开发者的旧消息历史")
        
        # 添加开发上下文
        self.developer.history_message_append(development_context)
        print(f"✅ 已添加开发上下文，开发者历史消息长度: {len(self.developer.history_message)}")
        
        # 开始多轮开发迭代
        for round_num in range(self.max_round):
            print(f"🔄 开发轮次 {round_num + 1}/{self.max_round}")
            
            # 动态调整token分配
            self._adjust_tokens_for_round(round_num)
            
            # 使用完整上下文进行开发
            try:
                project_files = self.developer.implement_project(architecture_plan, ui_design, 
                                                               self.project_files, round_num == 0)
            except Exception as e:
                error_str = str(e)
                # 检查是否为上下文长度超出限制的错误
                if "context_length_exceeded" in error_str or "maximum context length" in error_str:
                    print(f"⚠️ 第 {round_num + 1} 轮上下文长度超出，正在降低复杂度...")
                    # 清除开发者的消息历史（保留系统消息）
                    if hasattr(self.developer, 'history_message') and len(self.developer.history_message) > 1:
                        system_message = self.developer.history_message[0]
                        self.developer.history_message = [system_message]
                        # 重新添加上下文
                        self.developer.history_message_append(development_context)
                    
                    # 减少最大token数
                    self.current_max_tokens = max(self.current_max_tokens // 2, 256)
                    self.developer.max_tokens = self.current_max_tokens
                    
                    # 重试开发
                    try:
                        project_files = self.developer.implement_project(architecture_plan, ui_design, 
                                                                       self.project_files, round_num == 0)
                    except Exception as e2:
                        print(f"❌ 重试失败: {e2}")
                        if round_num == 0:
                            raise RuntimeError("初始开发失败")
                        else:
                            # 使用上一轮的文件
                            project_files = self.project_files
                            break
                else:
                    raise e
            
            # 检查开发结果
            if project_files == "error":
                if round_num == 0:
                    raise RuntimeError("初始开发失败")
                else:
                    # 使用上一轮的文件
                    project_files = self.project_files
                    break
            
            # 保存生成的文件
            self._save_project_files_with_tools(project_files)
            self.project_files = project_files
            
            print(f"📁 本轮生成文件: {list(project_files.keys())}")
            
            # 检查是否生成了真正的Web文件
            html_files = [f for f in project_files.keys() if f.endswith('.html')]
            css_files = [f for f in project_files.keys() if f.endswith('.css')]
            js_files = [f for f in project_files.keys() if f.endswith('.js')]
            
            print(f"📊 文件统计 - HTML: {len(html_files)}, CSS: {len(css_files)}, JS: {len(js_files)}")
            
            # 如果生成了完整的Web文件，可以提前结束
            if html_files and css_files and js_files:
                print("✅ 成功生成完整的Web项目！")
                break
            
            # 测试和反馈（最后一轮除外）
            if round_num < self.max_round - 1:
                print("🧪 使用自动化工具进行测试...")
                
                # 传统测试
                test_report = self.tester.test_project(project_files, architecture_plan)
                
                if test_report == "error":
                    print("⚠️ 测试失败，继续使用当前实现")
                    break
                
                # 增强的成功标准判断
                if ("all tests passed" in test_report.lower() or 
                    "no issues found" in test_report.lower()):
                    print("✅ 所有测试通过！项目成功完成。")
                    break
                
                # 提供反馈给开发者
                self.developer.receive_feedback(test_report)
        
        # 生成最终工具使用报告
        print("📊 生成最终工具使用报告...")
        tool_usage_report = self.tool_orchestrator.generate_report()
        self.session_history["tool_usage_report"] = tool_usage_report
        
        # 清理接口历史记录
        self.architect.itf.clear_history()
        self.developer.itf.clear_history() 
        self.tester.itf.clear_history()
        if hasattr(self.ui_designer, 'itf'):
            self.ui_designer.itf.clear_history()

        return self.project_files, self.session_history
        
    
    def _save_project_files(self, project_files):
        """Save generated project files to disk"""
        for file_path, content in project_files.items():
            full_path = os.path.join(self.output_dir, file_path)
            
            # Create directory if it doesn't exist
            dir_path = os.path.dirname(full_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            
            # Write file content
            try:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Saved: {file_path}")
            except Exception as e:
                print(f"Error saving {file_path}: {e}")
    
    def _save_project_files_with_tools(self, project_files):
        """Save project files with tool assistance and backup"""
        # Use file manager to organize files before saving
        organization_result = self.file_manager.execute(
            "organize_files",
            files=project_files,
            output_dir=self.output_dir
        )
        
        # Create backup if files already exist
        backup_result = self.file_manager.execute(
            "backup_existing",
            output_dir=self.output_dir
        )
        
        # Save files with the original method
        self._save_project_files(project_files)
        
        print(f"📁 File organization: {organization_result.get('status', 'completed')}")
        if backup_result.get('backup_created'):
            print(f"💾 Backup created: {backup_result.get('backup_path', 'N/A')}")
    
    def _generate_enhanced_feedback(self, traditional_report, automated_report, quality_report):
        """Generate simple, actionable feedback for the developer"""
        
        # Start with a simple structure
        issues = []
        
        # Check for test failures
        if automated_report.get("issues"):
            issues.extend(automated_report["issues"])
        
        # Traditional test issues
        if traditional_report and "error" in traditional_report.lower():
            issues.append("Fix syntax errors and runtime issues")
        
        # Generate simple feedback
        if not issues:
            return "✅ Good! Continue with current implementation approach."
        
        # Create actionable feedback
        feedback = "Please fix these issues:\n"
        for i, issue in enumerate(issues[:3], 1):  # Limit to 3 most important issues
            feedback += f"{i}. {issue}\n"
        
        feedback += "\nFocus on fixing issues for better results."
        return feedback


class FunctionSession(object):
    """Original function-level session for backwards compatibility"""
    def __init__(self, TEAM, ANALYST, PYTHON_DEVELOPER, TESTER, requirement, model='deepseek-chat', 
                 majority=1, max_tokens=512, temperature=0.0, top_p=0.95, max_round=4, before_func=''):

        self.session_history = {}
        self.max_round = max_round
        self.before_func = before_func
        self.requirement = requirement
        self.analyst = Analyst(TEAM, ANALYST, requirement, model, majority, max_tokens, temperature, top_p)
        self.coder = Coder(TEAM, PYTHON_DEVELOPER, requirement, model, majority, max_tokens, temperature, top_p)
        self.tester = Tester(TEAM, TESTER, requirement, model, majority, max_tokens, temperature, top_p)
    
    def run_session(self):
        # ... (keep original implementation from session.py)
        from session import Session
        original_session = Session(None, None, None, None, self.requirement, 
                                 model=self.analyst.model, majority=self.analyst.majority,
                                 max_tokens=self.analyst.max_tokens, temperature=self.analyst.temperature,
                                 top_p=self.analyst.top_p, max_round=self.max_round, 
                                 before_func=self.before_func)
        original_session.analyst = self.analyst
        original_session.coder = self.coder  
        original_session.tester = self.tester
        return original_session.run_session()
