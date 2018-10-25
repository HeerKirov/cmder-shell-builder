from json.decoder import JSONDecodeError
import json

CONFIG = 'config.json'
DEFAULT_COMMON = {
    "compile": ["bat"]
}
DEFAULT_LINE_HEAD = '[SELECT $+title]'
DEFAULT_LINE_ITEM = ' $index $title'
DEFAULT_LINE_SELECT = 'SELECT:'


class OutputError(Exception):
    def __init__(self, *args, **kwargs):
        super(OutputError, self).__init__(*args, **kwargs)


def get_or_raise(dictionary, key, raise_value):
        if key in dictionary:
            return dictionary[key]
        raise OutputError(raise_value)


def get_others(collection, *args):
    if isinstance(collection, dict):
        return dict((k, v) for (k, v) in collection.items() if k not in args)
    elif isinstance(collection, set):
        return set(i for i in collection if i not in args)
    elif isinstance(collection, list):
        return [i for i in collection if i not in args]
    else:
        return None


def find_condition(s, condition, start=0):
    for i in range(start, len(s)):
        if condition(s[i]):
            return i
    return -1


def format_string(string, **keymap):
    length = len(string)
    i = 0
    ret = ""
    while i < length:
        next_var = string.find('$', i)
        if next_var < 0:
            ret += string[i:]
            break
        else:
            if next_var > i:
                ret += string[i:next_var]
            over_var = find_condition(string,
                                      lambda c: not (c.isalpha() or c.isdigit() or c in ['_', '+', '-']),
                                      next_var + 1)
            if over_var == -1:
                over_var = length
            case_mode = 'normal'
            if next_var + 1 < over_var:
                if string[next_var + 1] == '+':
                    case_mode = 'upper'
                elif string[next_var + 1] == '-':
                    case_mode = 'lower'
            var = string[(next_var + 1) if case_mode == 'normal' else (next_var + 2):over_var]
            if var in keymap:
                value = str(keymap.get(var, None))
                if case_mode == 'upper':
                    value = value.upper()
                elif case_mode == 'lower':
                    value = value.lower()
                ret += value
            i = over_var
    return ret


class Choice(object):
    def __init__(self, **kwargs):
        self.toggle = get_or_raise(kwargs, 'toggle', 'toggle是choice中必须的属性。')
        self.terminal_title = get_or_raise(kwargs, 'terminal_title', 'terminal_title是choice中必须的属性。')
        self.command = get_or_raise(kwargs, 'command', 'command是choice中必须的属性。')
        self.keymap = get_others(kwargs, 'toggle', 'terminal_title', 'command')
        if 'title' not in self.keymap and 'toggle' in kwargs:
            toggle = kwargs['toggle']
            if isinstance(toggle, list) and len(toggle) > 0:
                first_toggle = toggle[0]
                self.keymap['title'] = str(first_toggle)


class FileConfig(object):
    def __init__(self, **kwargs):
        self.filename = get_or_raise(kwargs, 'filename', 'filename是configs中必须的属性。')
        self.title = get_or_raise(kwargs, 'title', 'title是configs中必须的属性。')
        self.use_index = kwargs.get('use_index', True)
        self.choices = [Choice(index=index + 1, **i) for index, i in enumerate(kwargs.get('choices', []))]
        self.__set_else_choice(kwargs.get('else_choice', None))
        self.__set_lines(kwargs.get('lines', None))
        self.keymap = get_others(kwargs, 'lines', 'use_index', 'choices', 'else_choice')

    def __set_else_choice(self, else_choice):
        self.else_choice = Choice(toggle=[], **else_choice) if else_choice is not None else None

    def __set_lines(self, lines):
        if lines is None:
            self.lines = {
                'head': DEFAULT_LINE_HEAD,
                'item': DEFAULT_LINE_ITEM,
                'select': DEFAULT_LINE_SELECT
            }
        else:
            self.lines = {
                'head': lines.get('head', DEFAULT_LINE_HEAD),
                'item': lines.get('item', DEFAULT_LINE_ITEM),
                'select': lines.get('select', DEFAULT_LINE_SELECT)
            }


class CmderShell(object):
    def __init__(self):
        self.__config = CmderShell.__load_config()
        self.__set_compile_goal()
        self.__set_file_configs()

    @staticmethod
    def __load_config():
        try:
            with open(CONFIG) as f:
                try:
                    return json.load(f)
                except JSONDecodeError:
                    raise OutputError('config文件解析发生错误。请检查文件的编写格式是否正确。')
        except FileNotFoundError:
            raise OutputError('config文件不存在。')

    def __set_compile_goal(self):
        common = self.__config.get('common', DEFAULT_COMMON)
        compile_goal = common.get('compile', None)
        if isinstance(compile_goal, list):
            self.__compile_goal = None if len(compile_goal) == 0 else compile_goal
        elif isinstance(compile_goal, str):
            self.__compile_goal = [compile_goal]
        else:
            self.__compile_goal = None

    def __set_file_configs(self):
        self.__file_configs = [FileConfig(**i) for i in self.__config.get('configs', [])]

    @staticmethod
    def __analyse_bat(file):
        ret = [
            '@echo off',
            'title=%s' % (file.title,),
            'echo %s' % (format_string(file.lines['head'], **file.keymap),),
            'echo.'
        ]
        for choice in file.choices:
            ret.append('echo %s' % (format_string(file.lines['item'], **choice.keymap)))
        ret.append('echo.')
        ret.append('set /p arg= echo %s' % (format_string(file.lines['select'], **file.keymap)))
        ret.append('cls')
        for i in range(0, len(file.choices)):
            choice = file.choices[i]
            if file.use_index:
                ret.append('if %%arg%%==%s goto f%s' % (i + 1, i))
            for t in choice.toggle:
                ret.append('if %%arg%%==%s goto f%s' % (t, i))
        ret.append('')
        if file.else_choice is not None:
            ret.append('title=%s' % (format_string(file.else_choice.terminal_title, **file.else_choice.keymap)))
            ret.append(format_string(file.else_choice.command, **file.else_choice.keymap))
            pass
        ret.append('exit')
        ret.append('')
        for i in range(0, len(file.choices)):
            choice = file.choices[i]
            ret.append(':f%s' % (i,))
            ret.append('    title=%s' % (format_string(choice.terminal_title, **choice.keymap),))
            ret.append('    %s' % (format_string(choice.command, **choice.keymap)))
            ret.append('    exit')
        return ret

    @staticmethod
    def __analyse_file(file, compile_goal):
        if compile_goal == 'bat':
            return CmderShell.__analyse_bat(file)
        else:
            raise OutputError('%s不是一个受支持的构建类型。' % (compile_goal,))

    @staticmethod
    def __write_file(filename, compile_goal, content):
        extension = {
            'bat': 'bat'
        }[compile_goal]
        with open('%s.%s' % (filename, extension), 'w') as f:
            for line in content:
                f.write(line + '\n')

    def run(self):
        if self.__compile_goal is not None:
            for file in self.__file_configs:
                for compile_goal in self.__compile_goal:
                    CmderShell.__write_file(file.filename, compile_goal, CmderShell.__analyse_file(file, compile_goal))
                    print('CmderShell: %s处理完毕。' % (file.filename,))
        else:
            print('CmderShell: 没有发现编译目标。因此执行被跳过。')


if __name__ == '__main__':
    try:
        CmderShell().run()
    except OutputError as e:
        raise e
