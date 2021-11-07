from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import Email
from socket import *
from email.base64mime import body_encode
import os
import base64

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = 'upload/'
bootstrap = Bootstrap(app)

# 选择一个邮件服务
mailServer = "smtp.qq.com"
# 创建客户端套接字并建立连接
serverPort = 587

# 发送方，验证信息，由于邮箱输入信息会使用base64编码，因此需要进行编码
username = "1402357917" + "@qq.com"  # 输入自己的用户名对应的编码
password = "jxkkqcyowwnqgfci"  # 此处不是自己的密码，而是开启SMTP服务时对应的授权码

endMsg = "\r\n.\r\n"
msgBoundary = "----=_mimePart_0"
contentBoundary = "------=_mimePart_0"
BasePath = "D:/Term/Final_Term/Main/计算机网络/实验课/实验3/smtp_email/upload"
CTE = "Content-Transfer-Encoding:base64\r\n\r\n"
# 草稿箱表单
data = {
    'fromAddress': '',
    'toAddress': '',
    'subject': '',
    'msg': '',
    'filepath': ''
}
send_info = []
contact_info = []


class EmailForm(FlaskForm):
    fromAddress = StringField('fromAddress', validators=[Email()])
    toAddress = StringField('toAddress')
    subject = StringField('subject')
    msg = TextAreaField('msg')
    submit = SubmitField("发送")


# 路由
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/send_email')
def to_page_email():
    return render_template('email.html')


@app.route('/copy')
def to_page_copy():
    return render_template('copy.html', data_dict=data)


@app.route('/contact')
def to_page_contact():
    return render_template('contact.html', data_dict=contact_info)


@app.route('/sendlist')
def to_page_sendlist():
    return render_template('sendlist.html', data_dict=send_info)


@app.route('/send', methods=['GET', 'POST'])
def sendEmail():
    form = EmailForm()
    if request.method == 'POST':
        fromAddress = str(request.form['fromAddress'])
        subject = str(request.form['subject'])
        msg = str(request.form['msg'])
        toAddress_list = str(request.form['toAddress'])
        toAddress = toAddress_list.split(";")
        # 获取所有上传的附件
        f_list = request.files.getlist("file")

        # 按了发送按钮
        if str(request.form['Submit']) == 'send_email':
            flag = True
            # 判断有无附件
            files = str(f_list[0])
            file_flag = files.split("'")[1]

            filepath = []
            attachmentType = []

            # 保存文件并存储路径,类型
            if file_flag != '':
                for f in f_list:
                    f.save(os.path.join(app.config['UPLOAD_FOLDER'], f.filename))
                    filepath.append(BasePath + "/" + f.filename)
                    file_list = str(f).split("'")
                    attachmentType.append(file_list[3])

            clientSocket = socket(AF_INET, SOCK_STREAM)
            clientSocket.connect((mailServer, serverPort))  # connect只能接收一个参数
            # 从客户套接字中接收信息
            recv = clientSocket.recv(1024).decode()
            print(recv)
            if '220' != recv[:3]:
                flag = False
                print('220 reply not received from server.')

            # 发送HELO命令并且打印服务端回复
            # 开始与服务器的交互，服务器将返回状态码250，说明请求动作正确完成
            heloCommand = 'HELO MY FRIEND\r\n'
            clientSocket.send(heloCommand.encode())  # 随时注意对信息编码和解码
            recv1 = clientSocket.recv(1024).decode()
            print(recv1)
            if '250' != recv1[:3]:
                flag = False
                print('250 reply not received from server.')

            # 发送 HELO 命令并且打印服务端回复
            # 开始与服务器的交互，服务器将返回状态码250,说明请求动作正确完成
            heloCommand = 'HELO MyName\r\n'
            clientSocket.send(heloCommand.encode())  # 随时注意对信息编码和解码
            recv1 = clientSocket.recv(1024).decode()
            print(recv1)
            if '250' != recv1[:3]:
                flag = False
                print('250 reply not received from server.')

            # 发送"AUTH LOGIN"命令，验证身份，服务器将返回状态码334(服务器等待用户输入验证信息)
            user_pass_encode64 = body_encode(f"\0{username}\0{password}".encode('ascii'), eol='')
            clientSocket.sendall(f'AUTH PLAIN {user_pass_encode64}\r\n'.encode())
            recv2 = clientSocket.recv(1024).decode()
            print(recv2)
            # 如果用户验证成功，服务器将返回状态码235
            if '235' != recv2[:3]:
                flag = False
                print('235 reply not received from server.')

            for ta in toAddress:
                # TCP连接建立好了之后，通过用户验证就可以开始发送邮件。邮件的传送从MAIL命令开始，MAIL命令后面附上发件人的地址。
                # 发送MAIL FROM命令，并包括发件人邮箱地址
                clientSocket.sendall(('MAIL FROM: <' + fromAddress + '>\r\n').encode())
                recvFrom = clientSocket.recv(1024).decode()
                print(recvFrom)
                if '250' != recvFrom[:3]:
                    flag = False
                    print('250 reply not received from server.')

                # 接着SMTP客户端发送一个或多个RCPT(收件人recipient的缩写)命令,格式为RCPT TO: <收件人地址>.
                # 发送RCPT TO 命令，并包含收件人邮箱地址，返回状态码250
                clientSocket.sendall(('RCPT TO: <' + ta + '>\r\n').encode())
                recvTo = clientSocket.recv(1024).decode()
                print(recvTo)
                if '250' != recvTo[:3]:
                    flag = False
                    print('250 reply not received from server.')

                # 发送DATA 命令，表示即将发送邮件内容。服务器将返回状态码354（开始邮件输入,以"."结束)
                clientSocket.send('DATA\r\n'.encode())
                recvData = clientSocket.recv(1024).decode()
                print(recvData)
                if '354' != recvData[:3]:
                    flag = False
                    print('354 reply not received from server.')

                message = 'from:' + fromAddress + '\r\n'
                clientSocket.sendall(message.encode())
                message = 'to: ' + ta + '\r\n'
                clientSocket.sendall(message.encode())
                message = 'subject: ' + subject + '\r\n'
                clientSocket.sendall(message.encode())
                message = 'Content-Type: ' + "multipart/mixed; " + "boundary=" + msgBoundary + '\r\n'
                clientSocket.sendall(message.encode())

                # 正文开始
                message = contentBoundary + '\r\n' + 'Content-Type: text/plain' + '\r\n\r\n'
                clientSocket.sendall(message.encode())
                message = msg + '\r\n'
                clientSocket.sendall(message.encode())
                # 附件
                # 判断有无附件
                if file_flag != '':
                    for f_index in range(len(filepath)):
                        if os.path.isfile(filepath[f_index]):
                            filename = os.path.basename(filepath[f_index])
                            message = contentBoundary + '\r\n' + 'Content-Type: ' + attachmentType[f_index] + '\r\n'
                            clientSocket.send(message.encode())
                            msgfilename = "Content-Disposition: attachment; filename=" + filename + ";" \
                                          + "filename*=utf-8''" \
                                          + filename + "\r\n"
                            clientSocket.send(msgfilename.encode())
                            clientSocket.send(CTE.encode())
                            clientSocket.send("\r\n".encode())
                            fb = open(filepath[f_index], 'rb')
                            while True:
                                filedata = fb.read(1024)
                                if not filedata:
                                    break
                                clientSocket.send(base64.b64encode(filedata))
                            # 重新设置文件读取指针到开头
                            fb.seek(0, 0)
                            fb.close()
                            clientSocket.send("\r\n".encode())

                message = contentBoundary + "--" + '\r\n'
                clientSocket.sendall(message.encode())
                # 以"."结束。请求成功返回250
                clientSocket.sendall(endMsg.encode())
                recvEnd = clientSocket.recv(1024).decode()
                print(recvEnd)
                if '250' != recvEnd[:3]:
                    flag = False
                    print('250 reply not received from server.')

            # 发送"QUIT" 命令,断开和邮件服务器的连接
            clientSocket.sendall('QUIT\r\n'.encode())
            clientSocket.close()

            # 保存至已发送
            if flag:
                send_element = {
                    'fromAddress': '',
                    'toAddress': '',
                    'subject': '',
                    'content': '',
                    'files': ''}
                send_files = ""
                for f in f_list:
                    if f.filename != "":
                        send_files += (f.filename + "; ")
                if send_files == "":
                    send_files = "没有附件"
                send_element['fromAddress'] = fromAddress
                send_element['subject'] = subject
                send_element['toAddress'] = toAddress_list
                send_element['content'] = msg
                send_element['files'] = send_files
                send_info.append(send_element)
                return render_template('sendlist.html', data_dict=send_info)
            else:
                return render_template('email.html', form=form)

        # 保存信件
        elif str(request.form['Submit']) == 'save_email':
            filepath = ""
            for f in f_list:
                filepath += BasePath + "/" + f.filename + "; "
            if filepath == BasePath + "/; ":
                filepath = ""
            data['fromAddress'] = fromAddress
            data['subject'] = subject
            data['msg'] = msg
            data['toAddress'] = toAddress_list
            data['filepath'] = filepath
            return render_template('copy.html', data_dict=data)

    return render_template('email.html', form=form)


@app.route('/edit_contact', methods=['GET', 'POST'])
def editContact():
    if request.method == 'POST':
        name = str(request.form['name'])
        address = str(request.form['address'])
        # 添加联系人
        if str(request.form['Submit']) == 'add':
            contact_list = {
                'name': name,
                'address': address
            }
            contact_info.append(contact_list)
        else:
            target_id = int(request.form['id'])
            # 删除
            if str(request.form['Submit']) == 'delete':
                del contact_info[target_id]
            # 编辑
            elif str(request.form['Submit']) == 'edit':
                if name != '':
                    contact_info[target_id]['name'] = name
                if address != '':
                    contact_info[target_id]['address'] = address

    return render_template('contact.html', data_dict=contact_info)
