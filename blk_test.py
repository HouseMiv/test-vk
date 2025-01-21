import subprocess
import argparse
import matplotlib.pyplot as plt
import json
import os

def run_fio_test(name, filename, output):
    """Запуск тестов fio с различными значениями iodepth и сохранение результатов."""
    iodepth_values = [1, 2, 4, 8, 16, 32, 64, 128, 256]
    results = {"iodepth": [], "latency": []}

    for iodepth in iodepth_values:
        print(f"Запуск теста {name} с iodepth={iodepth}")
        cmd = [
            "fio",
            f"--name={name}",
            f"--filename={filename}",
            "--ioengine=libaio",
            "--direct=1",
            "--rw=randread",  # Задаем тип операции: randread
            "--bs=4k",
            "--size=1G",
            "--numjobs=1",
            f"--iodepth={iodepth}",
            "--output-format=json",
        ]

        # Запускаем команду fio и захватываем результат
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Ошибка выполнения fio: {result.stderr}")
            continue

        # Извлечение средней задержки из результатов
        try:
            fio_output = json.loads(result.stdout)
            # Извлекаем среднюю задержку из "read" -> "lat_ns" -> "mean"
            latency = fio_output["jobs"][0]["read"]["lat_ns"]["mean"] / 1e6  # Преобразуем из наносекунд в миллисекунды
            results["iodepth"].append(iodepth)
            results["latency"].append(latency)
        except KeyError as e:
            print(f"Ошибка парсинга: ключ {e} отсутствует в выводе fio")
        except Exception as e:
            print(f"Ошибка: {e}")

    # Сохраняем график
    save_plot(results, output)


def save_plot(results, output):
    """Сохранение графика зависимости latency от iodepth."""
    if not results["iodepth"] or not results["latency"]:
        print("Ошибка: нет данных для построения графика.")
        return

    plt.figure()
    plt.plot(results["iodepth"], results["latency"], marker="o", label="randread")
    plt.title("Latency vs I/O Depth")
    plt.xlabel("I/O Depth")
    plt.ylabel("Latency (ms)")
    plt.xscale("log")  # Логарифмическая шкала для оси iodepth
    plt.grid(True)
    plt.legend()
    plt.savefig(output)
    print(f"График сохранен в {output}")


def parse_args():
    """Парсинг аргументов командной строки."""
    parser = argparse.ArgumentParser(description="Тестирование производительности блочного устройства.")
    parser.add_argument("--name", required=True, help="Имя теста")
    parser.add_argument("--filename", required=True, help="Путь к файлу для тестирования")
    parser.add_argument("--output", required=True, help="Путь для сохранения графика")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    print(f"Запуск теста: {args.name}")
    print(f"Файл для тестирования: {args.filename}")
    print(f"График будет сохранен в: {args.output}")

    # Проверка существования файла
    if not os.path.exists(args.filename):
        print(f"Ошибка: файл {args.filename} не найден.")
        exit(1)

    # Запуск теста
    run_fio_test(args.name, args.filename, args.output)
