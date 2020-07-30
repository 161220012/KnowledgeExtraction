from bs4 import BeautifulSoup
import urllib.request
import urllib.error
import urllib
import re
import chardet
movie_title_list=[]
summary_list=[]

# 分析网页内容
def analyze_douban(html):
    # print(html)
    soup = BeautifulSoup(html, "html.parser")
    movie_title = soup.find_all("div","title")  # 获取问题标题
    # print(len(movie_title))
    name_list=[]
    for movie in movie_title:
        movie_name=movie.get_text().replace("\n","")
        name_list.append(movie_name)
        # print(movie_name)
    new_name_list=[]
    for item in name_list:
        index=0
        for s in item:
            if s==' ':
               index+=1
            else:
                break
        item=item[index:len(item)]
        item=item.split(' ')[0]
        movie_title_list.append(item)
        # print(item)
    # print(name_list)
    next= soup.find("span","next")
    if next.find("link"):
        # print(next.find("link")['href'])
        return next.find("link")['href']
    else:
        return "NULL"

def analyze_baike(html,name):
    url_head = "https://baike.baidu.com"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0'}
    soup = BeautifulSoup(html, "html.parser")

    # 首先要检测是不是被百度自动跳转到错误页了
    error=soup.find("div","errorBox")
    if error!=None:
        return;

    # 处理爬取的页面本身是一个多义词需要选择url（例如baiku.baidu.com/item/小丑）
    poly_signal=soup.find("div","lemmaWgt-subLemmaListTitle")
    if poly_signal!=None:
        print(poly_signal)
        poly_table=soup.find("ul","custom_dot para-list list-paddingleft-1")
        poly_elem=poly_table.find_all("li")
        print(len(poly_elem))
        flag=0
        for i in range(len(poly_elem)):

            if re.match("(.*)[电影,影片,悬疑片]", poly_elem[i].get_text()) != None:
                flag=1
                print(poly_elem[i])
                url = url_head + poly_elem[i].find("a")['href']
                try:
                    req = urllib.request.Request(url=url, headers=headers)  # 同样进行伪装
                    html = urllib.request.urlopen(req, timeout=15).read().decode('utf-8')
                except urllib.error.HTTPError:
                        print('【HTTP ERROR】')
                except urllib.error.URLError:
                        print('【URL ERROR】')
                except socket.timeout:
                        print('【TIMEOUT ERROR】')
                except Exception:
                        print('【Unknown ERROR】')
                break
        if flag==0:
                return;

    soup = BeautifulSoup(html, "html.parser")
    polysemantList = soup.find("ul", class_="polysemantList-wrapper cmn-clearfix")
    # print(html)
    # print(polysemantList)
    # 处理多义词情况
    if polysemantList!=None:
        selected=polysemantList.find("span","selected")
        selected_text=selected.get_text()
        print(selected_text)

        # 若选对则不用管，选错则需要跳转到新的url
        if re.match("(.*)[电影,影片,悬疑片]",selected_text) == None:
            print("选错了")
            choices=polysemantList.find_all("li","item")
            # choices.remove(selected)
            flag=0
            for i in range(len(choices)):
                if re.match("(.*)[电影,影片,悬疑片]",choices[i].get_text())!=None:
                    print(choices[i])
                    flag=1
                    url=url_head+choices[i].find("a")['href']
                    # print(url)
                    try:
                        req = urllib.request.Request(url=url, headers=headers)  # 同样进行伪装
                        html = urllib.request.urlopen(req, timeout=15).read().decode('utf-8')
                    except urllib.error.HTTPError:
                        print('【HTTP ERROR】')
                    except urllib.error.URLError:
                        print('【URL ERROR】')
                    except socket.timeout:
                        print('【TIMEOUT ERROR】')
                    except Exception:
                        print('【Unknown ERROR】')
                    break
            # 如果发现没有就退出
            if flag==0:
                return;

    # print(html)
    soup = BeautifulSoup(html,"html.parser")
    summary = soup.find("div","lemma-summary")
    print(summary.get_text())
    summary_text=summary.get_text().replace("\n","").replace("本片","《"+name+"》").replace("该影片","《"+name+"》").replace("该片","《"+name+"》").replace("是","")
    summary_list.append(summary_text)

if __name__ == '__main__':
    # 伪装ip，防止被网站监测到爬虫程序
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0'}

    # 从豆瓣爬取电影名
    # url = 'https://www.douban.com/doulist/37430937/'
    #
    # while url !="NULL":
    #     try:
    #         req = urllib.request.Request(url=url, headers=headers)  # 同样进行伪装
    #         html = urllib.request.urlopen(req, timeout=15).read().decode('utf-8')
    #         url=analyze_douban(html)
    #     except urllib.error.HTTPError:
    #         print('【HTTP ERROR】')
    #     except urllib.error.URLError:
    #         print('【URL ERROR】')
    #     except socket.timeout:
    #         print('【TIMEOUT ERROR】')
    #     except Exception:
    #         print('【Unknown ERROR】')
    #
    # # print(movie_title_list)
    # # 电影名写进文件
    # with open("movie_list.txt","w",encoding="utf-8") as f:
    #     movie='\n'.join(movie_title_list)
    #     f.writelines(movie)

    # 将爬到的电影名去百度百科爬取资料,变量与前部分有重复使用，注释掉爬取豆瓣部分
    with open("movie_list.txt","r",encoding="utf-8") as f:
        for movie_name in f:
            movie_title_list.append(movie_name)
    # print(len(movie_title_list))
    url_head="https://baike.baidu.com/item/"
    for name in movie_title_list:
        # 务必记得去掉文件中的\n，否则无法得到正确url
        name=name.replace("\n","")
        #有极少部分特例不符合我们的爬取规则。。。
        # if name=="刺杀肯尼迪":
        #     name+="/8859233"
        name_str=name
        print(name)
        name = urllib.parse.quote(name)
        url = url_head+name
        # print(url)
        try:
            req = urllib.request.Request(url=url, headers=headers)  # 同样进行伪装
            html = urllib.request.urlopen(req, timeout=15).read().decode('utf-8')
            analyze_baike(html,name_str)
        except urllib.error.HTTPError:
            print('【HTTP ERROR】')
        except urllib.error.URLError:
            print('【URL ERROR】')
        except socket.timeout:
            print('【TIMEOUT ERROR】')
        except Exception:
            print('【Unknown ERROR】')


    with open("input.txt","w",encoding="utf-8") as f1:
        summary='\n\n'.join('%s' %id for id in summary_list)
        f1.writelines(summary)