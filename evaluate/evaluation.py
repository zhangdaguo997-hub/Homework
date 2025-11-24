# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import statistics
import numpy as np
from collections import defaultdict
import logging
from typing import List, Union
import itertools
from utils import build_test_method

logging.basicConfig(
    format="SystemLog: [%(asctime)s][%(name)s][%(levelname)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

def _dictionized_ground_truth_results(ground_truth_exec_results):
    ground_truth_results_by_task_and_solution = defaultdict(defaultdict)
    for result in ground_truth_exec_results:
        ground_truth_results_by_task_and_solution[result['task_id']][result['completion']] = result['passed']
    return ground_truth_results_by_task_and_solution

def _turn_solution_scores_into_choose_count(sorted_solution_scores, topk):
    wrapped = True if type(sorted_solution_scores[0][0]) == list else False
    result = []
    if wrapped:
        last_score = sorted_solution_scores[0][1]
        merged_solutions_and_score = [sorted_solution_scores[0]]
        for solutions, score in sorted_solution_scores[1:]:
            if score == last_score:
                last_solutions = merged_solutions_and_score[-1][0]
                merged_solutions_and_score[-1] = (last_solutions + solutions, score)
            else:
                merged_solutions_and_score.append((solutions, score))
                last_score = score
        for solutions_and_score in merged_solutions_and_score:
            result.append((solutions_and_score[0], 1))  # choose one from solutions_and_score
    else:
        topk_scores = sorted(list(set([i[1] for i in sorted_solution_scores])), reverse=True)
        for score in topk_scores:
            solutions = [s[0] for s in sorted_solution_scores if s[1] == score]
            result.append((solutions, 1))

    if len(result) >= topk:
        return result[:topk]
    else:
        intial_choose_count = [1]*len(result)
        for i in range(topk-len(result)):
            intial_choose_count[i%len(result)] += 1
        for i, choose_count in enumerate(intial_choose_count):
            result[i] = (result[i][0], choose_count)
        return result
    

def get_result_of_sorted_solutions(ground_truth_results_list, sorted_solutions_by_task, topks=[1,2,10]):
    # sorted_solutions_by_task {task_id: [([solutions], score), ...]}
    def _count_correct(solutions: list, ground_truth_results: dict) -> int:
        return sum([ground_truth_results[s] for s in solutions])
    
    ground_truth_results = _dictionized_ground_truth_results(ground_truth_results_list)
    topk_results = dict()
    for topk in topks:
        random_pass_at_k_by_task = pass_at_K_by_task(ground_truth_results_list, k=topk)
        pass_rates = []
        for task_id in ground_truth_results.keys():
            all_wrong_probability = 1
            if task_id in sorted_solutions_by_task and sorted_solutions_by_task[task_id]:
                solutions_and_probability = _turn_solution_scores_into_choose_count(sorted_solutions_by_task[task_id], topk)
                for solutions, choose_count in solutions_and_probability:
                    current_wrong_prob = _estimator(len(solutions), _count_correct(solutions, ground_truth_results[task_id]), 1)
                    repeat_current_wrong_prob = pow(current_wrong_prob, choose_count)
                    all_wrong_probability *= repeat_current_wrong_prob
                pass_rates.append(1-all_wrong_probability)
            else:
                pass_rates.append(random_pass_at_k_by_task[task_id])
        
        # the avg rate of all tasks
        topk_results[f'pass@{topk}'] = round(statistics.mean(pass_rates), 4)
    logger.info(topk_results)

def pass_at_K_by_task(results, k):
    result_dict = defaultdict(list)
    for line in results:
        result_dict[line['task_id']].append(line['passed'])
    result = dict()
    for task_id in result_dict.keys():
        total = len(result_dict[task_id])
        correct = sum(result_dict[task_id])
        score = _estimate_pass_at_k(total, [correct], k)[0]
        result[task_id] = score
    return result

def pass_at_K(results, k = [1, 10, 100]):
    """
    计算在不同k值下的pass@k指标
    
    Args:
        results: 测试结果列表，每个元素是一个字典，包含'task_id'和'passed'字段
        k: 要计算的k值列表，默认为[1, 10, 100]
    """
    def _turn_list_into_dict(result_lines):
        """
        将结果列表转换为按任务ID分组的字典
        
        Args:
            result_lines: 原始结果列表
            
        Returns:
            defaultdict: 键为任务ID，值为该任务的所有测试结果(bool列表)
        """
        result_dict = defaultdict(list)
        for line in result_lines:
            # 按任务ID分组，收集每个任务的测试结果
            result_dict[line['task_id']].append(line['passed'])
        return result_dict

    # 计算pass@k指标
    total, correct = [], []
    # 遍历每个任务的结果
    for passed in _turn_list_into_dict(results).values():
        total.append(len(passed))  # 记录每个任务的总样本数
        correct.append(sum(passed))  # 记录每个任务通过的样本数

    # 转换为numpy数组便于计算
    total = np.array(total)
    correct = np.array(correct)

    ks = k
    # 计算每个k值的pass@k指标
    pass_at_k = {f"pass@{k}": round(_estimate_pass_at_k(total, correct, k).mean(), 4)
                 for k in ks if (total >= k).all()}  # 只计算样本数足够大的k值
    logger.info(pass_at_k)  # 记录结果

def _estimator(n: int, c: int, k: int) -> float:
    """
    计算组合数比值: C(n-c, k) / C(n, k)
    用于估计在k次尝试中全部失败的概率
    
    Args:
        n: 总样本数
        c: 通过样本数
        k: 尝试次数
        
    Returns:
        float: 组合数比值
    """
    if n - c < k:
        return 0  # 如果失败样本数小于k，直接返回0
    # 计算组合数比值: ∏(1 - k/(n-c+1) * ... * (1 - k/n))
    return np.prod(1.0 - k / np.arange(n - c + 1, n + 1))

def _estimate_pass_at_k(
    num_samples: Union[int, List[int], np.ndarray],
    num_correct: Union[List[int], np.ndarray],
    k: int
) -> np.ndarray:
    """
    估计每个问题在k次尝试中至少通过一次的概率(pass@k)
    
    Args:
        num_samples: 每个问题的总样本数
        num_correct: 每个问题的通过样本数
        k: 尝试次数
        
    Returns:
        np.ndarray: 每个问题的pass@k估计值数组
    """
    # 处理输入参数类型，确保可以迭代
    if isinstance(num_samples, int):
        num_samples_it = itertools.repeat(num_samples, len(num_correct))
    else:
        assert len(num_samples) == len(num_correct)
        num_samples_it = iter(num_samples)

    # 计算每个问题的pass@k: 1 - 全部失败的概率
    return np.array([1.0 - _estimator(int(n), int(c), k) for n, c in zip(num_samples_it, num_correct)])




def AvgPassRatio(handled_solutions):
    total = len(handled_solutions)
    correct = sum([1 for s in handled_solutions if s['passed']])
    return correct/total
    

