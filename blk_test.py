import argparse
import subprocess
import os
import shutil
import matplotlib.pyplot as plt
import json

def run_fio_test(name, filename, output):
    """Запуск тестов fio с различными значениями iodepth и сохранение результатов."""
    iodepth_values = [1, 2, 4, 8, 16, 32, 64, 128, 256]
    results = {"iodepth": [], "latency_randread": [], "latency_randwrite": []}

    for iodepth in iodepth_values:
        print(f"Запуск теста {name} с iodepth={iodepth}")
        
        # Тест для randread
        cmd_read = [
            "fio",
            "--name=test",
            f"--filename={filename}",
            "--ioengine=libaio",
            "--direct=1",
            "--rw=randread",
            "--bs=4k",
            "--size=1G",
            "--numjobs=1",
            f"--iodepth={iodepth}",
            "--output-format=json",
        ]

        # Запуск команды fio для randread
        result_read = subprocess.run(cmd_read, capture_output=True, text=True)
        
        # Тест для randwrite
        cmd_write = [
            "fio",
            "--name=test",
            f"--filename={filename}",
            "--ioengine=libaio",
            "--direct=1",
            "--rw=randwrite",
            "--bs=4k",
            "--size=1G",
            "--numjobs=1",
            f"--iodepth={iodepth}",
            "--output-format=json",
        ]

        # Запуск команды fio для randwrite
        result_write = subprocess.run(cmd_write, capture_output=True, text=True)

        if result_read.returncode != 0 or result_write.returncode != 0:
            print(f"Ошибка выполнения fio: {result_read.stderr if result_read.returncode != 0 else result_write.stderr}")
            continue

        try:
            fio_output_read = json.loads(result_read.stdout)
            latency_read = fio_output_read["jobs"][0]["latency"]["mean"] / 1000  # Преобразуем в миллисекунды
            results["iodepth"].append(iodepth)
            results["latency_randread"].append(latency_read)

            fio_output_write = json.loads(result_write.stdout)
            latency_write = fio_output_write["jobs"][0]["latency"]["mean"] / 1000  # Преобразуем в миллисекунды
            results["latency_randwrite"].append(latency_write)
        except Exception as e:
            print(f"Ошибка парсинга вывода fio: {e}")

    # Сохраняем график
    save_plot(results, output)


def save_plot(results, output):
    """Сохранение графика зависимости latency от iodepth для randread и randwrite."""
    plt.figure()
    plt.plot(results["iodepth"], results["latency_randread"], marker="o", label="randread")
    plt.plot(results["iodepth"], results["latency_randwrite"], marker="o", label="randwrite")
    plt.title("Latency vs I/O Depth (randread & randwrite)")
    plt.xlabel("I/O Depth")
    plt.ylabel("Latency (ms)")
    plt.xscale("log")  # Логарифмическая шкала для оси iodepth
    plt.legend()
    plt.grid(True)
    plt.savefig(output)
    print(f"График сохранен в {output}")


def main():
    parser = argparse.ArgumentParser(description="Утилита для тестирования производительности блочного устройства.")
    parser.add_argument("--biktest-name", required=True, help="Имя теста")
    parser.add_argument("--biktest-filename", required=True, help="Путь до файла для тестирования")
    parser.add_argument("--biktest-output", required=True, help="Путь для сохранения графика")

    args = parser.parse_args()

    # Проверка существования файла для тестирования
    if not os.path.exists(args.biktest_filename):
        print(f"Ошибка: файл {args.biktest_filename} не найден.")
        return

    # Приведение путей к абсолютным
    args.biktest_filename = os.path.abspath(args.biktest_filename)
    args.biktest_output = os.path.abspath(args.biktest_output)

    # Проверка доступности fio
    if not shutil.which("fio"):
        print("Ошибка: утилита fio не установлена.")
        return

    # Запуск тестов
    run_fio_test(args.biktest_name, args.biktest_filename, args.biktest_output)


if __name__ == "__main__":
    main()
