import json


# Читаем из JSON
def read(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data


# Записываем в JSON
def write(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)