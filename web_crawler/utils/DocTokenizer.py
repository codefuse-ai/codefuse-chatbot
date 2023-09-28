
import re

# 非打印字符
NON_PRINTING_CHARS_RE = re.compile(
    f"[{''.join(map(chr, list(range(0, 32)) + list(range(127, 160))))}]"
)

class DocTokenizer():
    '''
    文档text处理器。
    '''

    def __init__(self):
        pass

    def doc_process(self, text):
        '''
        去除多余换行、去掉每行非打印字符和开头结尾空格
        '''
        # 去除多余换行
        text = self.remove_excess_lines(text)
        # 将文本拆分成行
        lines = text.split("\n")
        # 去掉每一行的开头和结尾的空格
        lines = [self.remove_non_printing_char_line(
            line.strip()) for line in lines]
        # 将行重新组合成文本
        text_new = "\n".join(lines)
        return text_new

    def remove_excess_lines(self, text):
        '''
        将2个以上的换行符替换为2个，html解析text时会产生大量换行\n
        '''
        pattern = r'\n\n+'
        return re.sub(pattern, '\n\n', text)

    def remove_non_printing_char_line(self, text):
        '''
        去除每一行的非打印字符
        '''
        return NON_PRINTING_CHARS_RE.sub("", text)
