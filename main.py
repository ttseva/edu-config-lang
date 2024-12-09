import json
import argparse
import sys
import re

def tokenize(expression):
    token_pattern = r'(\w+\(.*?\)|\w+|[+\-*])'
    return re.findall(token_pattern, expression)

def evaluate_expression(expression, constants):
    stack = []
    tokens = tokenize(expression)

    for token in tokens:
        if token.isidentifier():
            stack.append(get_constant_value(token, constants))
        elif token.lstrip('-').isdigit():
            stack.append(parse_number(token))
        elif token == '+':
            stack.append(perform_operation(stack, lambda a, b: a + b))
        elif token == '-':
            stack.append(perform_operation(stack, lambda a, b: a - b))
        elif token == '*':
            stack.append(perform_operation(stack, lambda a, b: a * b))
        elif token.startswith('concat(') and token.endswith(')'):
            stack.append(handle_concat(token[7:-1], constants))
        elif token.startswith('ord(') and token.endswith(')'):
            stack.append(handle_ord(token[4:-1], constants))
        else:
            raise ValueError(f"Неподдерживаемый токен: {token}")

    return stack[-1] if stack else None


def get_constant_value(token, constants):
    if token in constants:
        return constants[token]
    raise ValueError(f"Неизвестная константа: {token}")


def parse_number(token):
    return float(token) if '.' in token else int(token)


def perform_operation(stack, operation):
    b = stack.pop()
    a = stack.pop()
    return operation(a, b)


def handle_concat(params_str, constants):
    params = [p.strip() for p in params_str.split(',')]
    return ''.join(str(constants[p]) for p in params if p in constants)


def handle_ord(value, constants):
    value = value.strip()
    if value in constants:
        char_value = constants[value]
        if isinstance(char_value, str) and len(char_value) == 1:
            return ord(char_value)
        raise ValueError("Строка длиной > 1")
    raise ValueError(f"Неизвестная константа для ord: {value}")


def json_to_config(json_data):
    config_lines = []
    constants = {}

    for key, value in json_data.items():
        if key == "comment":
            config_lines.append(f"// {value}")
            continue
        if isinstance(value, str):
            config_lines.append(f'let {key} = @"{value}";')
            constants[key] = value
        elif isinstance(value, (int, float)):
            config_lines.append(f'let {key} = {value};')
            constants[key] = value
        elif isinstance(value, list):
            config_lines.append(f'{key} = [{", ".join(map(str, value))}];')
        elif isinstance(value, dict) and "expression" in value:
            result = evaluate_expression(value["expression"], constants)
            config_lines.append(f'let {value["name"]} = {result};')
        else:
            print(f"Неподдерживаемый тип данных для ключа '{key}'", file=sys.stderr)

    return "\n".join(config_lines)


def main():
    parser = argparse.ArgumentParser(description='Преобразование JSON в учебный конфигурационный язык.')
    parser.add_argument('--input', help='Путь к входному JSON файлу')
    parser.add_argument('--output', help='Путь к выходному файлу конфигурационного языка')

    args = parser.parse_args()

    try:
        with open(args.input, 'r', encoding='utf-8') as infile:
            json_data = json.load(infile)
    except (FileNotFoundError, json.JSONDecodeError) as err:
        print(f"Ошибка чтения: {err}")
        return

    try:
        config_data = json_to_config(json_data)
    except ValueError as err:
        print(f"Ошибка конвертации: {err}")
        return

    try:
        with open(args.output, 'w', encoding='utf-8') as outfile:
            outfile.write(config_data)
    except IOError as err:
        print(f"Ошибка записи: {err}")
        return

    print(f"Успешно! Конвертация записана в {args.output}")


if __name__ == "__main__":
    main()
