#!/usr/bin/env python3
"""
vLLM 性能测试脚本

功能：
- 默认自动执行三组测试：4k&1k 64、16k&1k 64、32k&1k 64
- 每组跑 5 轮，丢弃第 1 轮（warmup），取后 4 轮平均值
- 也支持通过命令行参数自定义单组测试
"""

import subprocess
import sys
import re
import json
import argparse
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# =============================================================================
# 服务配置（按需修改）
# =============================================================================
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 9091
MODEL_NAME = "MODEL_NAME"
TOKENIZER_PATH = "/path/to/tokenizer"

# =============================================================================
# 默认测试参数
# =============================================================================
DEFAULT_INPUT_LEN = 4096
DEFAULT_OUTPUT_LEN = 1024
DEFAULT_CONCURRENCY = 64
NUM_PROMPTS=256
TOTAL_ROUNDS = 5
OUTPUT_DIR = Path(f"./unit_test_output_{MODEL_NAME}")
ERROR_LOG_DIR = OUTPUT_DIR / "error_logs"

# =============================================================================
# 预设测试组：[(input_len, output_len, concurrency), ...]
# =============================================================================
PRESET_TEST_GROUPS = [
    (1024, 1024, 16),
    (4096, 1024, 16),
    (16384, 1024, 16),
    (32768, 1024, 64),
    (65536, 1024, 16),
    (65536, 1024, 32),
    (65536, 1024, 48),
    (65536, 1024, 52),
    (65536, 1024, 64),
]

# 输出解析正则表达式
METRIC_PATTERNS = {
    "Successful requests": r"Successful requests:\s+(\d+)",
    "Failed requests": r"Failed requests:\s+(\d+)",
    "Benchmark duration (s)": r"Benchmark duration \(s\):\s+([\d.]+)",
    "Total input tokens": r"Total input tokens:\s+(\d+)",
    "Total generated tokens": r"Total generated tokens:\s+(\d+)",
    "Request throughput (req/s)": r"Request throughput \(req/s\):\s+([\d.]+)",
    "Output token throughput (tok/s)": r"Output token throughput \(tok/s\):\s+([\d.]+)",
    "Total token throughput (tok/s)": r"Total token throughput \(tok/s\):\s+([\d.]+)",
    "Mean TTFT (ms)": r"Mean TTFT \(ms\):\s+([\d.]+)",
    "Median TTFT (ms)": r"Median TTFT \(ms\):\s+([\d.]+)",
    "P99 TTFT (ms)": r"P99 TTFT \(ms\):\s+([\d.]+)",
    "Mean TPOT (ms)": r"Mean TPOT \(ms\):\s+([\d.]+)",
    "Median TPOT (ms)": r"Median TPOT \(ms\):\s+([\d.]+)",
    "P99 TPOT (ms)": r"P99 TPOT \(ms\):\s+([\d.]+)",
    "Mean ITL (ms)": r"Mean ITL \(ms\):\s+([\d.]+)",
    "Median ITL (ms)": r"Median ITL \(ms\):\s+([\d.]+)",
    "P99 ITL (ms)": r"P99 ITL \(ms\):\s+([\d.]+)",
}


def save_error_log(cmd, input_len, output_len, concurrency, round_num, stdout, stderr, returncode):
    """当测试出现服务端报错时，保存完整的请求信息到错误日志文件"""
    ERROR_LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"error_in{input_len}_out{output_len}_c{concurrency}_round{round_num}_{timestamp}.json"
    filepath = ERROR_LOG_DIR / filename

    error_record = {
        "timestamp": datetime.now().isoformat(),
        "request_params": {
            "input_len": input_len,
            "output_len": output_len,
            "concurrency": concurrency,
            "num_prompts": NUM_PROMPTS,
            "round": round_num,
        },
        "command": " ".join(cmd),
        "command_list": cmd,
        "returncode": returncode,
        "stdout": stdout,
        "stderr": stderr,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(error_record, f, ensure_ascii=False, indent=2)

    print(f"  [ERROR LOG] 错误信息已保存到: {filepath}")


def parse_output(output):
    """解析 vllm bench serve 的输出文本，提取所有指标"""
    metrics = {}
    for key, pattern in METRIC_PATTERNS.items():
        match = re.search(pattern, output)
        if match:
            val = match.group(1)
            metrics[key] = float(val) if "." in val else int(val)
        else:
            metrics[key] = None
    return metrics


def build_command(input_len, output_len, concurrency):
    """构建 vllm bench serve 命令"""
    return [
        "vllm", "bench", "serve",
        "--host", SERVER_HOST,
        "--port", str(SERVER_PORT),
        "--model", MODEL_NAME,
        "--tokenizer", TOKENIZER_PATH,
        "--dataset-name", "random",
        "--random-input-len", str(input_len),
        "--random-output-len", str(output_len),
        "--endpoint", "/v1/completions",
        "--ignore-eos",
        "--trust-remote-code",
        "--num-prompts", str(NUM_PROMPTS),
        "--max-concurrency", str(concurrency),
    ]


def run_single_test(round_num, input_len, output_len, concurrency):
    """执行单轮测试并返回所有解析后的指标"""
    print(f"\n--- 第 {round_num}/{TOTAL_ROUNDS} 轮 ---")
    cmd = build_command(input_len, output_len, concurrency)
    print(f"  执行命令: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        # 检测服务端报错：returncode 非零 或 存在 Failed requests
        has_error = result.returncode != 0
        metrics = parse_output(result.stdout)
        failed_requests = metrics.get("Failed requests")
        if failed_requests is not None and failed_requests > 0:
            has_error = True

        if has_error:
            print(f"  错误: 第 {round_num} 轮执行失败 (returncode={result.returncode})")
            if result.stderr:
                print(f"  错误输出: {result.stderr[:200]}")
            save_error_log(
                cmd, input_len, output_len, concurrency, round_num,
                stdout=result.stdout, stderr=result.stderr, returncode=result.returncode
            )
            if result.returncode != 0:
                return None

        print(f"  第 {round_num} 轮完成")
        for key, val in metrics.items():
            if val is not None:
                print(f"    {key}: {val}")
        return metrics
    except FileNotFoundError:
        print("  错误: vllm 命令未找到，请确认 vllm 已安装且在 PATH 中")
        return None
    except Exception as e:
        print(f"  错误: 第 {round_num} 轮发生未知错误: {e}")
        save_error_log(
            cmd, input_len, output_len, concurrency, round_num,
            stdout="", stderr=str(e), returncode=-1
        )
        return None


def compute_average(all_round_metrics):
    """对后 4 轮的数值型指标取平均"""
    last4 = [m for m in all_round_metrics[1:] if m is not None]
    if not last4:
        return None

    avg = {}
    for key in METRIC_PATTERNS:
        values = [m[key] for m in last4 if m.get(key) is not None]
        if values:
            avg[key] = sum(values) / len(values)
        else:
            avg[key] = None
    return avg


def print_and_save_results(all_round_metrics, avg_metrics, input_len, output_len, concurrency):
    """打印每轮完整结果 + 后4轮平均值，并保存到文件"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"perf_results_in{input_len}_out{output_len}_c{concurrency}_{timestamp}.txt"
    filepath = OUTPUT_DIR / filename

    lines = []

    def out(text=""):
        print(text)
        lines.append(text)

    out("=" * 70)
    out("vLLM 性能测试结果")
    out(f"  服务: {SERVER_HOST}:{SERVER_PORT}")
    out(f"  模型: {MODEL_NAME}")
    out(f"  输入长度: {input_len}, 输出长度: {output_len}, 并发数: {concurrency}")
    out(f"  总轮数: {TOTAL_ROUNDS} (第1轮为warmup，取后4轮平均)")
    out(f"  执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    out("=" * 70)

    for i, metrics in enumerate(all_round_metrics):
        round_num = i + 1
        label = "（warmup，不计入平均）" if round_num == 1 else ""
        out(f"\n--- 第 {round_num} 轮 {label} ---")
        if metrics is None:
            out("  [FAILED]")
            continue
        for key, val in metrics.items():
            if val is not None:
                out(f"  {key}: {val}")

    out("\n" + "=" * 70)
    out("后 4 轮平均值")
    out("=" * 70)
    if avg_metrics is None:
        out("  无有效数据，无法计算平均值")
    else:
        for key, val in avg_metrics.items():
            if val is not None:
                out(f"  {key}: {val:.2f}")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"\n结果已保存至: {filepath}")


def run_test_group(input_len, output_len, concurrency, dry_run=False):
    """执行一组测试（5轮，取后4轮平均）"""
    print("\n" + "=" * 70)
    print(f"测试组: input_len={input_len}, output_len={output_len}, concurrency={concurrency}")
    print("=" * 70)

    if dry_run:
        cmd = build_command(input_len, output_len, concurrency)
        print(f"  命令: {' '.join(cmd)}")
        print(f"  将执行 {TOTAL_ROUNDS} 轮 (第1轮warmup，取后4轮平均)")
        return None

    all_round_metrics = []
    for round_num in range(1, TOTAL_ROUNDS + 1):
        metrics = run_single_test(round_num, input_len, output_len, concurrency)
        all_round_metrics.append(metrics)

    avg_metrics = compute_average(all_round_metrics)
    print_and_save_results(all_round_metrics, avg_metrics, input_len, output_len, concurrency)
    return avg_metrics


def main():
    parser = argparse.ArgumentParser(description="vLLM 性能测试脚本（5轮，取后4轮平均）")
    parser.add_argument("--input-len", type=int, default=None, help=f"输入长度 (指定后仅跑单组，跳过预设组)")
    parser.add_argument("--output-len", type=int, default=None, help=f"输出长度 (默认: {DEFAULT_OUTPUT_LEN})")
    parser.add_argument("--concurrency", type=int, default=None, help=f"并发数 (默认: {DEFAULT_CONCURRENCY})")
    parser.add_argument("--dry-run", action="store_true", help="仅打印命令，不执行")
    args = parser.parse_args()

    print("=" * 70)
    print("vLLM 性能测试")
    print(f"  服务: {SERVER_HOST}:{SERVER_PORT}")
    print(f"  模型: {MODEL_NAME}")
    print(f"  总轮数: {TOTAL_ROUNDS} (第1轮warmup，取后4轮平均)")
    print("=" * 70)

    if args.input_len is not None:
        # 用户指定了参数 → 只跑单组自定义测试
        input_len = args.input_len
        output_len = args.output_len if args.output_len is not None else DEFAULT_OUTPUT_LEN
        concurrency = args.concurrency if args.concurrency is not None else DEFAULT_CONCURRENCY
        run_test_group(input_len, output_len, concurrency, args.dry_run)
    elif args.dry_run:
        # dry-run 模式 → 打印所有预设组的命令
        print("\n[DRY RUN MODE] - 预设三组测试:\n")
        for input_len, output_len, concurrency in PRESET_TEST_GROUPS:
            cmd = build_command(input_len, output_len, concurrency)
            print(f"  input={input_len}, output={output_len}, concurrency={concurrency}")
            print(f"    {' '.join(cmd)}\n")
        print("[DRY RUN] 脚本验证完成，未实际执行测试。")
    else:
        # 默认模式 → 自动跑三组预设测试
        all_group_results = {}
        for input_len, output_len, concurrency in PRESET_TEST_GROUPS:
            avg = run_test_group(input_len, output_len, concurrency)
            all_group_results[(input_len, output_len, concurrency)] = avg

        # 汇总所有组的关键指标
        print("\n" + "=" * 70)
        print("全部测试完成 - 汇总")
        print("=" * 70)
        for (il, ol, c), avg in all_group_results.items():
            print(f"\n  input={il}, output={ol}, concurrency={c}:")
            if avg is None:
                print("    [FAILED]")
                continue
            for key in [
                "Request throughput (req/s)",
                "Output token throughput (tok/s)",
                "Mean TTFT (ms)",
                "P99 TTFT (ms)",
                "Mean TPOT (ms)",
                "P99 TPOT (ms)",
            ]:
                val = avg.get(key)
                if val is not None:
                    print(f"    {key}: {val:.2f}")


if __name__ == "__main__":
    main()
