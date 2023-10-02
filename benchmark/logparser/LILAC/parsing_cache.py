from collections import defaultdict, Counter, OrderedDict
import re
import sys

sys.setrecursionlimit(1000000)
from datetime import datetime
import multiprocessing as mp
import string

def print_tree(move_tree, indent=' '):
    for key, value in move_tree.items():
        if isinstance(value, dict):
            print(f'{indent}|- {key}')
            print_tree(value, indent + '|  ')
        elif isinstance(value, tuple):
            print(f'{indent}|- {key}: tuple')
        else:
            print(f'{indent}|- {key}: {value}')


def lcs_similarity(X, Y):
    m, n = len(X), len(Y)
    c = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if X[i - 1] == Y[j - 1]:
                c[i][j] = c[i - 1][j - 1] + 1
            else:
                c[i][j] = max(c[i][j - 1], c[i - 1][j])
    return 2 * c[m][n] / (m + n)


class ParsingCache(object):
    def __init__(self):
        self.template_tree = {}
        self.template_list = []
    
    def add_templates(self, event_template, insert=True, relevant_templates=[]):

            # if "<*>" not in event_template:
            #     self.template_tree["$CONSTANT_TEMPLATE$"][event_template] = event_template
            #     continue
            # original_template = event_template
            # event_template = self._preprocess_template(event_template)
            #print("event template after preprocess: ", event_template)
        template_tokens = message_split(event_template)
        if not template_tokens or event_template == "<*>":
            return -1
        if insert or len(relevant_templates) == 0:
            id = self.insert(event_template, template_tokens, len(self.template_list))
            self.template_list.append(event_template)
            return id
        # print("relevant templates: ", relevant_templates)
        max_similarity = 0
        similar_template = None
        for rt in relevant_templates:
            splited_template1, splited_template2 = rt.split(), event_template.split()
            if len(splited_template1) != len(splited_template2):
                continue 
            similarity = lcs_similarity(splited_template1, splited_template2)
            if similarity > max_similarity:
                max_similarity = similarity
                similar_template = rt
        if max_similarity > 0.8:
            success, id = self.modify(similar_template, event_template)
            if not success:
                id = self.insert(event_template, template_tokens, len(self.template_list))
                self.template_list.append(event_template)
            return id
        else:
            id = self.insert(event_template, template_tokens, len(self.template_list))
            self.template_list.append(event_template)
            return id
            #print("template tokens: ", template_tokens)
            
    def insert(self, event_template, template_tokens, template_id):
        start_token = template_tokens[0]
        if start_token not in self.template_tree:
            self.template_tree[start_token] = {}
        move_tree = self.template_tree[start_token]

        tidx = 1
        while tidx < len(template_tokens):
            token = template_tokens[tidx]
            if token not in move_tree:
                move_tree[token] = {}
            move_tree = move_tree[token]
            tidx += 1

        move_tree["".join(template_tokens)] = (
            sum(1 for s in template_tokens if s != "<*>"),
            template_tokens.count("<*>"),
            event_template,
            template_id
        )  # statistic length, count of <*>, original_log, template_id
        return template_id

    def modify(self, similar_template, event_template):
        with open ("modify.txt", "a") as fa:
            fa.write("=====================================\n")
            fa.write(similar_template + "\n")
            fa.write(event_template + "\n")
            fa.write("=====================================\n")
        merged_template = []
        similar_tokens = similar_template.split()
        event_tokens = event_template.split()
        i = 0
        print(similar_template)
        print(event_template)
        for token in similar_tokens:
            print(token, event_tokens[i])
            if token == event_tokens[i]:
                merged_template.append(token)
            else:
                merged_template.append("<*>")
            i += 1
        merged_template = " ".join(merged_template)
        print("merged template: ", merged_template)
        success, old_ids = self.delete(similar_template)
        if not success:
            with open("error_modify.txt", "a") as fa:
                fa.write("=====================================\n")
                fa.write(similar_template + "\n")
                fa.write(event_template + "\n")
                fa.write("=====================================\n")
            print("Error: cannot delete old template")
            return False, -1
        self.insert(merged_template, message_split(merged_template), old_ids)
        self.template_list[old_ids] = merged_template
        return True, old_ids
        
    
    def delete(self, event_template):
        template_tokens = message_split(event_template)
        start_token = template_tokens[0]
        if start_token not in self.template_tree:
            return False, []
        move_tree = self.template_tree[start_token]

        tidx = 1
        while tidx < len(template_tokens):
            token = template_tokens[tidx]
            if token not in move_tree:
                return False, []
            move_tree = move_tree[token]
            tidx += 1
        old_id = move_tree["".join(template_tokens)][3]
        del move_tree["".join(template_tokens)]
        return True, old_id


    def match_event(self, log):
        return tree_match(self.template_tree, log)


    def _preprocess_template(self, template):
        # template = re.sub("<NUM>", "<*>", template)
        # print("T1: ", template)
        # if template.count("<*>") > 50:
        #     first_start_pos = template.index("<*>")
        #     template = template[0 : first_start_pos + 3]
        # # print("T2: ", template)
        return template


# def replace_punctuation(text):
#     pattern = r'(?<!<\*)[.,!?;:{}[\]()+-](?!<\*>)'
#     result = re.sub(pattern, ' ', text)
#     return result


# def replace_punctuation_manual(text):
#     new_text = ""
#     max_len = len(text)
#     i = 0
#     while i < max_len:
#         #if text[i] in string.punctuation:
#         if text[i] in string.punctuation:
#             if text[i] == "<":
#                 if text[i + 1] == "*" and text[i + 2] == ">":
#                     new_text += " <*> "
#                     i += 3
#                     continue
#             new_text += text[i]
#         else:
#             new_text += text[i]
#         i += 1
#     return new_text


def post_process_tokens(tokens, punc):
    excluded_str = ['=', '|', '(', ')']
    for i in range(len(tokens)):
        if tokens[i].find("<*>") != -1:
            tokens[i] = "<*>"
        else:
            new_str = ""
            for s in tokens[i]:
                if (s not in punc and s != ' ') or s in excluded_str:
                    new_str += s
            tokens[i] = new_str
    return tokens


#splitter_regex = re.compile("(<\*>|[^A-Za-z])")
def message_split(message):
    #print(string.punctuation)
    punc = "!\"#$%&'()+,-/:;=?@.[\]^_`{|}~"
    #print(punc)
    #punc = re.sub("[*<>\.\-\/\\]", "", string.punctuation)
    splitters = "\s\\" + "\\".join(punc)
    #print(splitters)
    #splitters = "\\".join(punc)
    # splitter_regex = re.compile("([{}]+)".format(splitters))
    splitter_regex = re.compile("([{}])".format(splitters))
    #print("Before replace: ", message)
    #print("After replace: ", message)
    tokens = re.split(splitter_regex, message)
    #print("tokens :", tokens)
    # new_tokens = []
    # for token in tokens:
    #     print("t:   ", token)
    #     split_token = re.split(r"([.]*)", token)
    #     for t in split_token:
    #         if t != '':
    #             new_tokens.append(t)
    # tokens = new_tokens
    # print("new tokens: ", tokens)
    tokens = list(filter(lambda x: x != "", tokens))
    
    #print("tokens: ", tokens)
    tokens = post_process_tokens(tokens, punc)
    #message = replace_punctuation_manual(message)
    #tokens = message.split()
    # for i in range(len(tokens)):
    #     if tokens[i].find("<*>") != -1:
    #         tokens[i] = "<*>"
    #print("tokens: ", tokens)
    tokens = [
        token.strip()
        for token in tokens
        if token != "" and token != ' ' 
    ]
    tokens = [
        token
        for idx, token in enumerate(tokens)
        if not (token == "<*>" and idx > 0 and tokens[idx - 1] == "<*>")
    ]
    #print("tokens: ", tokens)
    #tokens = [token.strip() for token in message.split()]
    #print(tokens)
    return tokens


# def pre_process_log(log):
#     tokens = message_split(log)
#     return ' '.join(tokens)


def tree_match(match_tree, log_content):
    #print("Worker {} start matching {} lines.".format(os.getpid(), len(log_list)))
        # if not "is false" in log_content: continue
        # Full match
        # if log_content in match_tree["$CONSTANT_TEMPLATE$"]:
        #     log_template_dict[log_content] = (log_content, [])
        #     continue

    log_tokens = message_split(log_content)
        #print("log tokens: ", log_tokens)
    template, template_id, parameter_str = match_template(match_tree, log_tokens)
    if template:
        return (template, template_id, parameter_str)
    else:
        return ("NoMatch", "NoMatch", parameter_str)


def match_template(match_tree, log_tokens):
    results = []
    find_results = find_template(match_tree, log_tokens, results, [], 1)
    # print(find_results)
    relevant_templates = find_results[1]
        # print(relevant_templates)
    # print(find_results)
    # print("results: ", results)
    if len(results) > 1:
        new_results = []
        for result in results:
            if result[0] is not None and result[1] is not None and result[2] is not None:
                new_results.append(result)
    else:
        new_results = results
    if len(new_results) > 0:
        if len(new_results) > 1:
            new_results.sort(key=lambda x: (-x[1][0], x[1][1]))
        return new_results[0][1][2], new_results[0][1][3], new_results[0][2]
    return False, False, relevant_templates


def get_all_templates(move_tree):
    result = []
    for key, value in move_tree.items():
        if isinstance(value, tuple):
            result.append(value[2])
        else:
            result = result + get_all_templates(value)
    return result


def find_template(move_tree, log_tokens, result, parameter_list, depth):
    # print("=====================================")
    # print(log_tokens)
    # print_tree(move_tree)
    # print("=====================================")
    flag = 0 # no futher find
    if len(log_tokens) == 0:
        for key, value in move_tree.items():
            if isinstance(value, tuple):
                result.append((key, value, tuple(parameter_list)))
                flag = 2 # match
        if "<*>" in move_tree:
            parameter_list.append("")
            move_tree = move_tree["<*>"]
            if isinstance(move_tree, tuple):
                result.append(("<*>", None, None))
                flag = 2 # match
            else:
                for key, value in move_tree.items():
                    if isinstance(value, tuple):
                        result.append((key, value, tuple(parameter_list)))
                        flag = 2 # match
        # return (True, [])
    else:
        token = log_tokens[0]

        relevant_templates = []
        
        if token in move_tree:
            find_result = find_template(move_tree[token], log_tokens[1:], result, parameter_list,depth+1)
            if find_result[0]:
                flag = 2 # match
            elif flag != 2:
                flag = 1 # futher find but no match
                # print("find_result: ", find_result)
                relevant_templates = relevant_templates + find_result[1]
        if "<*>" in move_tree:
            if isinstance(move_tree["<*>"], dict):
                next_keys = move_tree["<*>"].keys()
                next_continue_keys = []
                for nk in next_keys:
                    nv = move_tree["<*>"][nk]
                    if not isinstance(nv, tuple):
                        next_continue_keys.append(nk)
                idx = 0
                # print("len : ", len(log_tokens))
                while idx < len(log_tokens):
                    # if idx == len(log_tokens) - 1:
                        # print(log_tokens[idx])
                    token = log_tokens[idx]
                    # print("try", token)
                    if token in next_continue_keys:
                        # print("add", "".join(log_tokens[0:idx]))
                        parameter_list.append("".join(log_tokens[0:idx]))
                        # print("End at", idx, parameter_list)
                        find_result = find_template(
                            move_tree["<*>"], log_tokens[idx:], result, parameter_list,depth+1
                        )
                        if find_result[0]:
                            flag = 2 # match
                        elif flag != 2:
                            flag = 1 # futher find but no match
                            # relevant_templates = relevant_templates + find_result[1]
                        if parameter_list:
                            parameter_list.pop()
                        # print("back", parameter_list)
                    idx += 1
                if idx == len(log_tokens):
                    parameter_list.append("".join(log_tokens[0:idx]))
                    find_result = find_template(
                        move_tree["<*>"], log_tokens[idx + 1 :], result, parameter_list,depth+1
                    )
                    if find_result[0]:
                        flag = 2 # match
                    else:
                        if flag != 2:
                            flag = 1
                        relevant_templates = relevant_templates + find_result[1]
                    if parameter_list:
                        parameter_list.pop()
    if flag == 2:
        return (True, [])
    if flag == 1:
        return (False, relevant_templates)
    if flag == 0:
        # print(log_tokens, flag)
        if depth >= 2:
            return (False, get_all_templates(move_tree))
        else:
            return (False, [])
        


if __name__ == "__main__":
    #result = message_split("chrome.exe - proxy.cse.cuhk.edu.hk:5070 close, 1293 bytes (1.26 KB) sent, 2437 bytes (2.37 KB) received, lifetime <1 sec")
    #print(result)
    #exit(0)
    templates = [
        "This is a test template, haha",
# Failed to fetch remote block <*> from BlockManagerId(<*>, <*>, <*>) (failed attempt <*>)
    ]
    #print(pre_process_log("Bad protocol version identification '<*>' from <*> port <*>"))
    #exit(0)
    cache = ParsingCache()

    for template in templates:
        cache.add_templates(template)
    print(cache.template_tree)    

    cache.add_templates("This is a run template, haha", False, ["This is a test template, haha"])
    print(cache.template_tree)
    # print_tree(cache.template_tree)
    #print(Tree.template_tree['reverse'])
    # print(Tree.template_tree)
    logs = [
        #"test=1, user=3",
        # "test=1, user=4, ruser=3",
        # "-[NETClientConnection effectiveBundleID] using process name ksfetch as bundle ID (this is expected for daemons without bundle ID good enough"
        # "Hello, this is test"
        #"test=1, user=3",
        #"test=1, user=4, ruser=3",
        #"OK",
        #"Connect",
        #"Connect to ok, true",
        #"Connect to ok failed",
        "proxy.cse.cuhk.edu.hk:5070 close, 0 bytes sent, 0 bytes received, lifetime <1 sec"
    ]
    for log in logs:
        print(cache.match_event(log))
