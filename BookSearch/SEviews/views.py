from django.shortcuts import render
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from SEviews.models import Books #导入数据库更改这里
from search.matrix import Matrix
# Create your views here.

from django.http import HttpResponse
from django.shortcuts import render,render_to_response

m = Matrix()

#字符串函数处理主函数
def SE_Result(wd):
    return list(m.tiered_search(wd))

#获取数目内容
def SE_Recom(bid):
    return list(m.find_most_similar(bid))

#对简介长度进行裁剪
def summary_cut(book_list, summary_len=110):
    for book in book_list:
        if book.summary.split()[0].isalpha():
            if len(book.summary)>=summary_len * 2:
                book.summary=book.summary[:summary_len * 2 - 3]+"..."
        else:
            if len(book.summary)>=summary_len:
                book.summary=book.summary[:summary_len - 3]+"..."
        book.tags = book.tags.split()
    #return book_list

#对推荐书目过长标题进行裁剪
def title_cut(book_list, title_len=10):
    for book in book_list:
        if all((word.isalpha() or word.isdigit() for word in book.title.split())):
            if len(book.title)>=title_len * 2:
                book.title=book.title[:title_len*2-3]+"..."
        else:
            if len(book.title)>=title_len:
                book.title=book.title[:title_len-3]+"..."

#响应搜索请求主要函数
def result(request):
    #推荐书表
    try:
        wd = str(request.GET.get('wd','')) #查询字段
        page = int(request.GET.get('page','1')) #页码接受
    except ValueError:
        page = 1
        wd = ''
    #空白查询回首页
    if wd=='':
        return render(request,'index.html')
    #结果搜寻
    else:
        posts_list = SE_Result(wd)                   #处理数据并返回列表
        recom_list = SE_Recom(posts_list[:5])                    #获取推荐书表
        page_size=6                                      #每页显示条目
        paginator = Paginator(posts_list, page_size)     #页码器
        try:
            bids = paginator.page(page)                 #页码选择
        except (EmptyPage, InvalidPage):
            bids = paginator.page(paginator.num_pages)
        posts = []
        recoms= []
        startPos = (page-1)*page_size
        endPos   = startPos + page_size
        #读取搜索结果
        if posts_list:
            for id in posts_list[startPos:endPos]:
                book = Books.objects.filter(bid=id)
                if len(book)>=1:
                    book[0].img_url = 'img/{}.jpg'.format(book[0].bid)
                    posts.append(book[0])
            none = 0
        #读取推荐书目
        else:
            none = 1
        for re in recom_list:
            book = Books.objects.filter(bid=re)
            if len(book)>=1:
                book[0].img_url = 'img/{}.jpg'.format(book[0].bid)
                recoms.append(book[0])
        title_cut(recoms)
        summary_cut(posts)
        title = wd + " _SynJauNeng"                         #标题
        return render_to_response( 'res.html',
        {'name':title,
         'wd':wd,
         'none':none,
         'posts':posts,
         'pages':bids,
         'recoms':recoms,
         'pid':page,
         'items': len(posts_list)})          #字典传递变量

def index(request):
    return render(request, 'index.html')
