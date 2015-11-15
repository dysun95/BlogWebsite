# -*- coding: utf-8 -*-

import tornado.httpserver
import tornado.auth
import tornado.ioloop
import tornado.options
import tornado.web
import os.path
import datetime
import mysql.connector

from tornado.options import define, options
define("port", default=8880, help="run on the given port", type=int)
define("db_name", default="blogwebsite", help="database", type=str)
define("db_user", default="root", help="user", type=str)
define("db_pass", default="123456", help="password", type=str)



class Application(tornado.web.Application):
	def __init__(self):
		tornado.web.Application.__init__(self,
			handlers=[(r"/",LoginHandlers),
				(r"/logout",LogoutHandlers),
				(r"/register",RegisterHandlers),
				(r"/write",WriteHandlers),
				(r"/blog",BlogHandlers),
				(r"/delete",DeleteHandlers)
				],
			template_path=os.path.join(os.path.dirname(__file__),"templates"),
			static_path=os.path.join(os.path.dirname(__file__),"static"),
			cookie_secret="CkwXIkG6RXs15skVeMBhdbJKt0QSqk1tivD1smsr98Y="
			)

conn=mysql.connector.connect(user=options.db_user,password=options.db_pass,database=options.db_name)
cursor=conn.cursor()

class BaseHandlers(tornado.web.RequestHandler):
	def get_current_user(self):
		return self.get_secure_cookie("username")

#登录模块
class LoginHandlers(BaseHandlers):
	def get(self):
		if self.current_user is  None:
			self.render("login.html")
		else:
			self.redirect('/blog')

	def post(self):
		username=self.get_argument("username",None)
		userpassword=self.get_argument("userpassword",None)
		cursor.execute('SELECT * FROM userinfo WHERE username=%s and userpassword=%s',[username,userpassword])
		user=cursor.fetchall()
		if len(user) is 0:
			self.finish("error")
		else:
			self.set_secure_cookie("username", username)
			self.redirect('/blog')

#注册模块
class RegisterHandlers(BaseHandlers):
	def get(self):
		self.render("register.html")

	def post(self):
		id=0
		input_username=self.get_argument("username",None)
		userpassword=self.get_argument("userpassword",None)
		confirm_userpassword=self.get_argument("confirm_userpassword",None)
		if confirm_userpassword==userpassword and input_username:
			cursor.execute('CREATE TABLE IF NOT EXISTS userinfo(id int,username varchar(20),userpassword varchar(20))')
			cursor.execute('SELECT * FROM userinfo')
			user=cursor.fetchall()
			if user:
				cursor.execute('SELECT * FROM userinfo WHERE username=%s',[input_username])
				user=cursor.fetchall()
				if user:
					pass
				else:
					cursor.execute('SELECT max(id) FROM userinfo')
					maxid=cursor.fetchall()
					print (maxid)
					print (maxid[0][0])
					if maxid[0][0]>=0:
						id=maxid[0][0]+1
						print (id)
					cursor.execute('INSERT INTO userinfo(id,username,userpassword) values(%s,%s,%s)',[id,input_username,userpassword])
					conn.commit()
			else:
				print ('b')
				cursor.execute('INSERT INTO userinfo(id,username,userpassword) values(%s,%s,%s)',[id,input_username,userpassword])
				conn.commit()
			self.redirect('/')
		else:
			self.redirect('/register')

#注销模块
class LogoutHandlers(BaseHandlers):
    def get(self):
        self.clear_cookie("username")
        print ('logout')
        self.redirect("/")

#写博客模块
class WriteHandlers(BaseHandlers):
	def get(self):
		self.render("write.html")

	def post(self):
		title=self.get_argument("title",None)
		content=self.get_argument("content",None)
		id=0
		if title and content:
			cursor.execute('CREATE TABLE IF NOT EXISTS bloglist(id int,title varchar(100),content varchar(600),date varchar(20))')
			cursor.execute('SELECT max(id) FROM bloglist')
			maxid=cursor.fetchall()
			print (maxid)
			if maxid[0][0]!=None:
				if maxid[0][0]>=0:
					id=maxid[0][0]+1
			cursor.execute('INSERT INTO bloglist(id,title,content,date) values(%s,%s,%s,%s)',[id,title,content,datetime.datetime.now().strftime('%y-%m-%d %I:%M:%S %p')])
			conn.commit()
			self.redirect('/blog')
		else:
			self.redirect('/write')

#博客列表模块
class BlogHandlers(BaseHandlers):
	def get(self):
		cursor.execute('CREATE TABLE IF NOT EXISTS bloglist(id int,title varchar(100),content varchar(600),date varchar(20))')
		cursor.execute('SELECT * FROM bloglist ORDER BY date')
		bloglist=cursor.fetchall()
		print (bloglist)
		blog=[]
		if bloglist:
			for row in bloglist:
				blog.append(dict(id=row[0],title=row[1],content=row[2],date=row[3]))
			if blog:
				self.render("blog.html",blogs=blog)
		else:
			self.render("blog.html",blogs=(dict(id=-1,title="无",content="空",date="00-00-00 00:00:00 AM"),))

class DeleteHandlers(BaseHandlers):
	def post(self):
		cursor.execute('DELETE FROM bloglist')
		conn.commit()
		self.redirect('/blog')

def main():
	http_server=tornado.httpserver.HTTPServer(Application())
	http_server.listen(options.port)
	tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
	main()