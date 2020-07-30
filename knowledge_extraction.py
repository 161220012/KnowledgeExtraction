# coding=utf-8
import re
from pyltp import Segmentor, Postagger, Parser, NamedEntityRecognizer
from pprint import pprint

segmentor = Segmentor()
segmentor.load_with_lexicon("./pyltp_models/cws.model", './construct_dict.txt')
# segmentor.load("./ltp_data/cws.model")  # 分词模型
postagger = Postagger()
postagger.load("./pyltp_models/pos.model")  # 词性标注
parser = Parser()
parser.load("./pyltp_models/parser.model")  # 依存句法分析
recognizer = NamedEntityRecognizer()
recognizer.load("./pyltp_models/ner.model")  # 命名实体识别

in_file_name = "sentences.txt"
out_file_name = "output.txt"
in_file = open(in_file_name, 'r', encoding="utf-8")
out_file = open(out_file_name, 'w+', encoding="utf-8")

construct_list = []

relation_list=[]
total_person_list=[]
person_list=[]
total_institution_list=[]
institution_list=[]
total_movie_list=[]
movie_list=[]

other_list=[]



def get_contruct_list():
    f = open('construct_dict.txt', 'r', encoding="utf-8")
    for line in f:
        construct = line.strip()
        if construct not in construct_list:
            construct_list.append(construct)

def get_movie_list():
    f = open('movie_list.txt','r',encoding='utf-8')
    for line in f:
        movie = line.strip()
        if movie not in total_movie_list:
            total_movie_list.append(movie)


def map_WordList_ConstructList(word_list):
    for word in word_list:
        if word in construct_list:
            return True
    return False
    # return True


def extraction_start():
    """
    事实三元组抽取的总控程序
    """
    for sentence_index, text_line in enumerate(in_file):
        sentence = text_line.strip()
        if len(sentence) == 0:
            continue
        fact_knowledge_extract(sentence, sentence_index)
    segmentor.release()
    in_file.close()
    out_file.close()


def post_processing(words):
    post_processing_words=[]
    start=0         #组合分词的头部index
    offset=0        #组合分词的偏移量
    index=0         #循环指针

    while index<len(words):
        flag=0
        for word in construct_list:
            item = words[index]
            issuccess=0
            flag = 1
            if len(item) > len(word):
                flag = 0
            else :
                for i in range(0, len(item)):
                    if item[i]!=word[i]:
                        flag=0

            if flag==1:                 #可能找到命名实体的头部
                if len(item)==len(word):    #分词正确，继续检查下一个词
                    post_processing_words.append(item)
                    index=index+1
                    break
                for seek_index in range(index+1,len(words)):
                    item=item+words[seek_index]
                    if len(item) > len(word):
                        flag = 0
                    else:
                        for j in range(0, len(item)):
                            if item[j] != word[j]:
                                flag = 0
                    if flag==0:         #如果发现不是该命名实体，则跳出循环继续搜寻下一个词
                        break
                    if item==word:      #发现完整命名实体，跳出循环
                        post_processing_words.append(item)
                        index = seek_index+1
                        issuccess=1
                        break
                if issuccess==1:
                    break

        if flag==0:
            post_processing_words.append(words[index])
            index=index+1


    return post_processing_words

def fact_knowledge_extract(sentence, sentence_index):
    """
    对于给定的句子进行事实三元组抽取
    Args:
        sentence: 要处理的语句
    """
    words = segmentor.segment(sentence)
    words=post_processing(words)
    postags = postagger.postag(words)
    netags = recognizer.recognize(words, postags)
    arcs = parser.parse(words, postags)

    child_dict_list = build_parse_child_dict(words, postags, arcs)

    print("\t".join(words))
    print("\t".join(postags))
    print('\t'.join(netags))
    # print("\t".join("%d:%s" % (arc.head, arc.relation) for arc in arcs))
    for i in range(len(child_dict_list)):
        print(i,words[i],postags[i],netags[i],"%d:%s" % (arcs[i].head-1, arcs[i].relation),child_dict_list[i])
    print('========================')

    for index in range(len(postags)):
        # 尝试抽取人名和机构名
        if netags[index][0] == 'S' or netags[index][0] == 'B':
            ni = index

            if netags[ni][0] == 'B':
                for i in range(index, len(postags)):
                    if netags[i][0] == 'E':
                        ni = i
                        break
                # while ni < len(postags) and netags[ni][0] != 'E':
                #     ni += 1
                e1 = ''.join(words[index:ni + 1])
            else:
                e1 = words[ni]
            if netags[ni][3] == 'h':
                if e1 not in total_person_list:
                    total_person_list.append(e1)
            elif netags[ni][3] == 'i':
                if e1 not in total_institution_list:
                    total_institution_list.append(e1)

    for index in range(len(postags)):
        # 抽取以谓词为中心的事实三元组
        if postags[index] == 'v':
            child_dict = child_dict_list[index]
            # 主谓宾
            if 'SBV' in child_dict and 'VOB' in child_dict:
                # print(index, words[index])
                cur_wordlist = []
                e1 = complete_entity(words, postags, child_dict_list, child_dict['SBV'][0], cur_wordlist)
                r = words[index]
                e2 =''
                for i in range(len(child_dict['VOB'])):
                    e2 += complete_entity(words, postags, child_dict_list, child_dict['VOB'][i], cur_wordlist)
                # print('==================================')
                # print(cur_wordlist)
                # print(e1)
                # print(r)
                # print(e2)

                if (map_WordList_ConstructList(cur_wordlist)):
                    # out_file.write("主语谓语宾语关系\t({}, {}, {})\t{}\n".format(e1, r, e2, sentence_index))
                    if r not in relation_list:
                        relation_list.append(r)

                    if e1 in total_movie_list:
                        if e1 not in movie_list:
                            movie_list.append(e1)
                    elif e1 in total_institution_list:
                        if e1 not in institution_list:
                            institution_list.append(e1)
                    elif e1 in total_person_list:
                        if e1 not in person_list:
                            person_list.append(e1)
                    elif e1 not in other_list:
                        other_list.append(e1)

                    out_file.write("({}, {}, {})\n".format(e1, r, e2))
                    out_file.flush()

                if 'COO' in child_dict:  # 寻找并列关系 其实还可以再并列
                    for j in range(len(child_dict['COO'])):
                        tie_index = child_dict['COO'][j]
                        new_child_dict = child_dict_list[tie_index]
                        if 'VOB' in new_child_dict:
                            cur_wordlist = []
                            if 'SBV' in new_child_dict:
                                e1 = complete_entity(words, postags, child_dict_list, new_child_dict['SBV'][0], cur_wordlist)
                            else:
                                e1= complete_entity(words, postags, child_dict_list, child_dict['SBV'][0], cur_wordlist)
                            r = words[tie_index]
                            e2 = ''
                            for i in range(len(new_child_dict['VOB'])):
                                e2 += complete_entity(words, postags, child_dict_list, new_child_dict['VOB'][i], cur_wordlist)
                            # print('==================================')
                            # print(e1)
                            # print(r)
                            # print(e2)
                            if (map_WordList_ConstructList(cur_wordlist)):
                                # out_file.write("并列主语谓语宾语关系\t({}, {}, {})\t{}\n".format(e1, r, e2, sentence_index))
                                if r not in relation_list:
                                    relation_list.append(r)

                                if e1 in total_movie_list:
                                    if e1 not in movie_list:
                                        movie_list.append(e1)
                                elif e1 in total_institution_list:
                                    if e1 not in institution_list:
                                        institution_list.append(e1)
                                elif e1 in total_person_list:
                                    if e1 not in person_list:
                                        person_list.append(e1)
                                elif e1 not in other_list:
                                    other_list.append(e1)

                                out_file.write("({}, {}, {})\n".format(e1, r, e2))
                                out_file.flush()

            # 定语后置，动宾关系
            # if arcs[index].relation == 'ATT':
            #     if 'VOB' in child_dict:
            #         cur_wordlist = []
            #         e1 = complete_entity(words, postags, child_dict_list, arcs[index].head - 1, cur_wordlist)
            #         r = words[index]
            #         e2 = complete_entity(words, postags, child_dict_list, child_dict['VOB'][0], cur_wordlist)
            #         temp_string = r+e2
            #         if temp_string == e1[:len(temp_string)]:
            #             e1 = e1[len(temp_string):]
            # #         print('==================================')
            # #         print(e1)
            # #         print(r)
            # #         print(e2)
            #         if temp_string not in e1:
            #             if (map_WordList_ConstructList(cur_wordlist)):
            #                 out_file.write("定语后置动宾关系\t({}, {}, {})\t{}\n".format(e1, r, e2, sentence_index))
            #                 # out_file.write("({}, {}, {})\n".format(e1, r, e2))
            #                 out_file.flush()

            # 宾语前置关系
            if 'FOB' in child_dict and 'ADV' in child_dict:
                cur_wordlist = []
                r = words[index]
                e2 = complete_entity(words, postags, child_dict_list, child_dict['FOB'][0], cur_wordlist)
                for j in range(len(child_dict['ADV'])):
                    new_index= child_dict['ADV'][j]
                    new_child_dict = child_dict_list[new_index]
                    if 'POB' in new_child_dict:
                        e1 = complete_entity(words, postags, child_dict_list, new_child_dict['POB'][0], cur_wordlist)
                        if 'CMP' in child_dict:
                            e2 += complete_entity(words, postags, child_dict_list, child_dict['CMP'][0], cur_wordlist)

                        if (map_WordList_ConstructList(cur_wordlist)):
                            # out_file.write("宾语前置关系\t({}, {}, {})\t{}\n".format(e1, r, e2, sentence_index))
                            if r not in relation_list:
                                relation_list.append(r)

                            if e1 in total_movie_list:
                                if e1 not in movie_list:
                                    movie_list.append(e1)
                            elif e1 in total_institution_list:
                                if e1 not in institution_list:
                                    institution_list.append(e1)
                            elif e1 in total_person_list:
                                if e1 not in person_list:
                                    person_list.append(e1)
                            elif e1 not in other_list:
                                other_list.append(e1)

                            if e2 in total_movie_list:
                                if e2 not in movie_list:
                                    movie_list.append(e2)
                            elif e2 in total_institution_list:
                                if e2 not in institution_list:
                                    institution_list.append(e2)
                            elif e2 in total_person_list:
                                if e2 not in person_list:
                                    person_list.append(e2)
                            elif e2 not in other_list:
                                other_list.append(e2)

                            out_file.write("({}, {}, {})\n".format(e1, r, e2))
                            out_file.flush()
                if 'COO' in child_dict:
                    new_child_dict = child_dict_list[child_dict['COO'][0]]
                    r= words[child_dict['COO'][0]]
                    if 'SBV' in new_child_dict:
                        e1=complete_entity(words,postags,child_dict_list,new_child_dict['SBV'][0],cur_wordlist)
                        if (map_WordList_ConstructList(cur_wordlist)):
                            # out_file.write("宾语前置关系\t({}, {}, {})\t{}\n".format(e1, r, e2, sentence_index))
                            if r not in relation_list:
                                relation_list.append(r)

                            if e1 in total_movie_list:
                                if e1 not in movie_list:
                                    movie_list.append(e1)
                            elif e1 in total_institution_list:
                                if e1 not in institution_list:
                                    institution_list.append(e1)
                            elif e1 in total_person_list:
                                if e1 not in person_list:
                                    person_list.append(e1)
                            elif e1 not in other_list:
                                other_list.append(e1)

                            if e2 in total_movie_list:
                                if e2 not in movie_list:
                                    movie_list.append(e2)
                            elif e2 in total_institution_list:
                                if e2 not in institution_list:
                                    institution_list.append(e2)
                            elif e2 in total_person_list:
                                if e2 not in person_list:
                                    person_list.append(e2)
                            elif e2 not in other_list:
                                other_list.append(e2)

                            out_file.write("({}, {}, {})\n".format(e1, r, e2))
                            out_file.flush()


            # 含有介宾关系的主谓动补关系
            if 'SBV' in child_dict and 'CMP' in child_dict:
                cur_wordlist = []
                e1 = complete_entity(words, postags, child_dict_list, child_dict['SBV'][0], cur_wordlist)
                cmp_index = child_dict['CMP'][0]
                r = words[index] + words[cmp_index]
                e2=''
                if 'POB' in child_dict_list[cmp_index]:
                    for i in range(len(child_dict_list[cmp_index]['POB'])):
                        e2 += complete_entity(words, postags, child_dict_list, child_dict_list[cmp_index]['POB'][i], cur_wordlist)
                    # print('==================================')
                    # print(e1)
                    # print(r)
                    # print(e2)
                    if (map_WordList_ConstructList(cur_wordlist)):
                        # out_file.write("介宾关系主谓动补\t({}, {}, {})\t{}\n".format(e1, r, e2, sentence_index))
                        if r not in relation_list:
                            relation_list.append(r)

                        if e1 in total_movie_list:
                            if e1 not in movie_list:
                                movie_list.append(e1)
                        elif e1 in total_institution_list:
                            if e1 not in institution_list:
                                institution_list.append(e1)
                        elif e1 in total_person_list:
                            if e1 not in person_list:
                                person_list.append(e1)
                        elif e1 not in other_list:
                            other_list.append(e1)

                        out_file.write("({}, {}, {})\n".format(e1, r, e2))
                        out_file.flush()

        # 尝试抽取命名实体有关的三元组
        if netags[index][0] == 'S' or netags[index][0] == 'B':
            ni = index

            if netags[ni][0] == 'B':
                for i in range(index, len(postags)):
                    if netags[i][0] == 'E':
                        ni = i
                        break
                # while ni < len(postags) and netags[ni][0] != 'E':
                #     ni += 1
                e1 = ''.join(words[index:ni+1])
            else:
                e1 = words[ni]

            # print(e1)

            if arcs[ni].relation == 'ATT' and postags[arcs[ni].head-1] == 'n' and netags[arcs[ni].head-1] == 'O':
                # print(words[ni])
                # print(arcs[ni].head)
                # print(words[arcs[ni].head-1])
                cur_wordlist = []
                r = complete_entity(words, postags, child_dict_list, arcs[ni].head-1, cur_wordlist)
                # print(r)
                if e1 in r:
                    r = r[(r.index(e1)+len(e1)):]
                    # print(r)
                if arcs[arcs[ni].head-1].relation == 'ATT' and netags[arcs[arcs[ni].head-1].head-1] != 'O':
                    # e2 = complete_entity(words, postags, child_dict_list, arcs[arcs[ni].head-1].head-1, cur_wordlist)
                    e2=words[arcs[arcs[ni].head-1].head-1]
                    # print(e2)
                    mi = arcs[arcs[ni].head-1].head-1
                    li = mi
                    if netags[mi][0] == 'B':
                        while netags[mi][0] != 'E':
                            mi += 1
                        e = ''.join(words[li+1:mi+1])
                        e2 += e
                    if r in e2:
                        e2 = e2[(e2.index(r)+len(r)):]
                    # print('==================================')
                    # print(e1)
                    # print(r)
                    # print(e2)
                    # if r+e2 in sentence:
                    #     out_file.write("人名//地名//机构\t(%s, %s, %s)\n" % (e1, r, e2))
                    # out_file.write("人名//地名//机构\t(%s, %s, %s)\n" % (e1, r, e2))

                    if e2 in total_movie_list:
                        if e2 not in movie_list:
                            movie_list.append(e2)
                    elif e2 in total_institution_list:
                        if e2 not in institution_list:
                            institution_list.append(e2)
                    elif e2 in total_person_list:
                        if e2 not in person_list:
                            person_list.append(e2)
                    elif e2 not in other_list:
                        other_list.append(e2)

                    out_file.write("(%s, %s, %s)\n" % (e1, r, e2))
                    out_file.flush()

    extract_person_construction(words, postags, netags, arcs)


def extract_person_construction(words, postags, netags, arcs):
    child_dict_list = build_parse_child_dict(words, postags, arcs)
    for index in range(len(postags)):
        if netags[index][0] == 'S':
            pre_child_dict = child_dict_list[index - 1]
            if 'ATT' in pre_child_dict:
                first_entity_index = pre_child_dict['ATT'][0]
                if 'ATT' in child_dict_list[first_entity_index]:
                    e1_index = child_dict_list[first_entity_index]['ATT'][0]
                    e1 = complete_construction(words, child_dict_list, e1_index, True) + words[first_entity_index]
                    relation = complete_construction(words, child_dict_list, index - 1, False)
                    e2 = words[index]
                    # out_file.write("人名//职位//机构\t(%s, %s, %s)\n" % (e1, relation, e2))

                    if e2 in total_movie_list:
                        if e2 not in movie_list:
                            movie_list.append(e2)
                    elif e2 in total_institution_list:
                        if e2 not in institution_list:
                            institution_list.append(e2)
                    elif e2 in total_person_list:
                        if e2 not in person_list:
                            person_list.append(e2)
                    elif e2 not in other_list:
                        other_list.append(e2)

                    out_file.write("(%s, %s, %s)\n" % (e1, relation, e2))

                if 'LAD' in pre_child_dict:  # 并列结构
                    for lad_entity_index in pre_child_dict['LAD']:
                        tie_entity_index = lad_entity_index - 1
                        if 'ATT' in child_dict_list[tie_entity_index]:
                            e1_index = child_dict_list[tie_entity_index]['ATT'][0]
                            e1 = complete_construction(words, child_dict_list, e1_index, True)
                            relation = complete_construction(words, child_dict_list, tie_entity_index, False)
                            e2 = words[index]
                            # out_file.write("人名//职位//机构\t(%s, %s, %s)\n" % (e1, relation, e2))
                            if e2 in total_movie_list:
                                if e2 not in movie_list:
                                    movie_list.append(e2)
                            elif e2 in total_institution_list:
                                if e2 not in institution_list:
                                    institution_list.append(e2)
                            elif e2 in total_person_list:
                                if e2 not in person_list:
                                    person_list.append(e2)
                            elif e2 not in other_list:
                                other_list.append(e2)
                            out_file.write("(%s, %s, %s)\n" % (e1, relation, e2))


def complete_construction(words, child_dict_list, word_index, is_head):
    child_dict = child_dict_list[word_index]
    prefix = ''
    postfix= ''
    if 'ATT' in child_dict:
        if is_head:
            for i in child_dict['ATT']:
                prefix += words[i]
        else:
            for i in child_dict['ATT'][1:]:
                prefix += words[i]

    return prefix + words[word_index] + postfix


def build_parse_child_dict(words, postags, arcs):
    """
    为句子中的每个词语维护一个保存句法依存儿子节点的字典
    Args:
        words: 分词列表
        postags: 词性列表
        arcs: 句法依存列表, head表示父节点索引，relation表示依存弧的关系
    """
    child_dict_list = []
    for index in range(len(words)):
        child_dict = {}
        for arc_index in range(len(arcs)):
            if arcs[arc_index].head == index + 1:
                relation = arcs[arc_index].relation
                if relation not in child_dict:
                    child_dict[relation] = []
                child_dict[relation].append(arc_index)
        child_dict_list.append(child_dict)
    return child_dict_list


def complete_entity(words, postags, child_dict_list, word_index, wordlist):
    """
    完善识别的部分实体
    """

    child_dict = child_dict_list[word_index]
    prefix = ''
    postfix = ''
    tie_entity = ''

    key_list=child_dict.keys()
    # print(key_list)
    for item in key_list:
        if item=='ATT':
            for i in range(len(child_dict['ATT'])):
                prefix += complete_entity(words, postags, child_dict_list, child_dict['ATT'][i], wordlist)

        if item=='POB':
            for i in range(len(child_dict['POB'])):
                postfix += complete_entity(words, postags, child_dict_list, child_dict['POB'][i], wordlist)

        if postags[word_index] == 'v' or postags[word_index]=='p':

            if item=='CMP':
                postfix += complete_entity(words, postags, child_dict_list, child_dict['CMP'][0], wordlist)

            if item=='VOB':
                for i in range(len(child_dict['VOB'])):
                    postfix += complete_entity(words, postags, child_dict_list, child_dict['VOB'][i], wordlist)
            if item=='SBV':
                prefix += complete_entity(words, postags, child_dict_list, child_dict['SBV'][0], wordlist)
            if item=='ADV':
                for i in range(len(child_dict['ADV'])):
                    prefix += complete_entity(words, postags,child_dict_list, child_dict['ADV'][i],wordlist)
            if item=='FOB':
                prefix  = complete_entity(words, postags, child_dict_list, child_dict['FOB'][0], wordlist) +prefix

        if item == 'LAD':
            prefix+=complete_entity(words,postags,child_dict_list,child_dict['LAD'][0],wordlist)
        if item == 'RAD':
            postfix += complete_entity(words, postags, child_dict_list, child_dict['RAD'][0], wordlist)


        if item=='COO':
            for i in range(len(child_dict['COO'])):
                tie_entity += complete_entity(words, postags, child_dict_list, child_dict['COO'][i], wordlist)
            if len(tie_entity) > 0:
                tie_entity = '|' + tie_entity
    wordlist.append(words[word_index])
    return prefix + words[word_index] + postfix + tie_entity


def doc2sent():
    with open('input.txt', 'r', encoding='utf-8') as in_file, open('sentences.txt', 'w', encoding='utf-8') as temp_file:
        inputs = in_file.read()
        sents = re.split('[。]', inputs)
        sents = '\n'.join(sents)
        temp_file.writelines(sents)

def create_person_list():
    with open('person_list.txt', 'w', encoding='utf-8') as f:
        people = '\n'.join(total_person_list)
        f.writelines(people)

def create_institution_list():
    with open('institution_list.txt', 'w', encoding='utf-8') as f:
        institutions='\n'.join(total_institution_list)
        f.writelines(institutions)

def triple2nt():
    with open('output.txt', 'r', encoding='utf-8') as f, open('data.nt', 'w', encoding='utf-8') as out:
        triples = []
        for line in f:
            s, p, o = line.rstrip('\n')[1:-1].split(', ')
            # if '|' in s:
            #     continue
            if '|' in p:
                p1, p2 = p.split('|')
                triples.append((s, p1, o))
                triples.append((s, p2, o))
            else:
                triples.append((s, p, o))
        for s, p, o in triples:
            out.write(
                '<http://ws.nju.edu.cn/tcqa#%s>\t<http://ws.nju.edu.cn/tcqa#%s>\t<http://ws.nju.edu.cn/tcqa#%s>.\n' % (
                s, p, o))
        for p in relation_list:
            out.write('<http://ws.nju.edu.cn/tcqa#%s>\t<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>\t<http://www.w3.org/1999/02/22-rdf-syntax-ns#Relation>.\n' % (
                p))

        for person in person_list:
            out.write('<http://ws.nju.edu.cn/tcqa#%s>\t<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>\t<http://ws.nju.edu.cn/tcqa#Person>.\n' % (person))

        for institution in institution_list:
            out.write('<http://ws.nju.edu.cn/tcqa#%s>\t<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>\t<http://ws.nju.edu.cn/tcqa#Institution>.\n' % (institution))

        for movie in movie_list:
            out.write('<http://ws.nju.edu.cn/tcqa#%s>\t<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>\t<http://ws.nju.edu.cn/tcqa#Movie>.\n' % (movie))

        for other in other_list:
            out.write('<http://ws.nju.edu.cn/tcqa#%s>\t<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>\t<http://ws.nju.edu.cn/tcqa#Other>.\n' % (other))

        # 标记实体类别
        out.write(
            '<http://ws.nju.edu.cn/tcqa#Person> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2000/01/rdf-schema#Class>.\n')
        out.write(
            '<http://ws.nju.edu.cn/tcqa#Institution> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2000/01/rdf-schema#Class>.\n')
        out.write(
            '<http://ws.nju.edu.cn/tcqa#Movie> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2000/01/rdf-schema#Class>.\n')
        out.write(
            '<http://ws.nju.edu.cn/tcqa#Other> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2000/01/rdf-schema#Class>.\n')

if __name__ == "__main__":
    doc2sent()
    get_contruct_list()
    get_movie_list()
    extraction_start()
    create_person_list()
    create_institution_list()
    triple2nt()
