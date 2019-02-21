# kd163blogBackUp
python3加pyqt5做的网易博客备份工具,适用于linux系统和window系统.

#使用方法
下载源代码
配置python3环境
使用pip安装pyqt5库
python3 kd163blogBackUp.py

# 依赖项
- pyqt5
- python3

# 下载原理
## 心情随笔
通过dwr的方式(本质就是http请求吧)调用接口http://api.blog.163.com/{}/dwr/call/plaincall/FeelingsBeanNew.getRecentFeelingCards.dwr ,{}是需要替换的博客名,入参里设置需要下载的心情随笔条数(c0-param1和c0-param2)即可得到一个js文件.

最后通过正则表达式解析js文件的内容就可以到心情随笔的内容.

心情随笔的评论是通过同样的方式调用接口http://api.blog.163.com/{}/dwr/call/plaincall/FeelingsBeanNew.getRecentFeelingsComment.dwr 得到的.

## 博客正文
通过dwr的方式访问http://api.blog.163.com/{}/dwr/call/plaincall/BlogBeanNew.getBlogsNewTheme.dwr ,获得指定数量的博客的下载链接,然后通过http的方式直接获取单篇博客的html,最后通过beautiful soap库获取html里的图片img标签,下载所有的图片,保存到跟博客文章的标题同名的目录下.

图片的链接,第一位是指定图片从哪台服务器下载,有些两种服务器,有些有photo前缀,有些没有.需要注意

最后,通过正则表达式,将所有的图片下载链接替换为本地目录的地址.

## 相册
相册功能已不再维护,新建立了一个项目来继续维护相册的功能.地址:https://github.com/bkdwei/kd163PhotoDownloader

# 截图
![kd163blogBackUp_screenshot](https://github.com/bkdwei/kd163blogBackUp/blob/master/doc/kd163blogBackUp_screenshot.jpg "截图")

# 作者
坤东