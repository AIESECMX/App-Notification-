#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
from gis_token_generator import GIS
import datetime
import json
import config
from multiprocessing import Pool
from contextlib import closing
from app_data import App
import smtplib
from smtplib import SMTPException
from smtplib import SMTP
from email.mime.text import MIMEText
from email.MIMEImage import MIMEImage
import requests
#import progressbar
import sys  

reload(sys)  
sys.setdefaultencoding('utf8')



##CONSTANTS

#to init we just get the acces token from expa with MC permissions
token_genrator = GIS()
token = token_genrator.generate_token(config.EXPA_USER, config.EXPA_PASS)
mail_html = open('mail.html','r').read()
yesterday = datetime.date.today()-datetime.timedelta(2)
headers = {'access_token': token,
'filters[created_at][from]':yesterday.strftime('%y-%m-%d'),
'filters[created_at][to]':yesterday.strftime('%y-%m-%d'),
'page':1,
'filters[status]':'open'}
sender = config.MAIL_USER

#this method will send a notificaciton fot he opp managers and ep managers
def appNotificacion( page = 1):
	
	
	r = requests.get("https://gis-api.aiesec.org/v2/applications.json", data=headers)
	#print 'aplications '+str(r.status_code)
	message = json.loads(r.text)
	apps = message['data']
	#cuantas paginas de applicaciones hay que pedir
	extra_pages = message['paging']['total_pages']
	print (('numero de paginas :'+str(extra_pages)))
	#time to process the apps we got

	# the original inteniro was to launch a few threads here
	# TODO : send several threads instead of just one
	#launching multiple threads
	#pool = Pool(processes=10)       
	#pool=Pool(5)       
	#pool.map(getApps, range(1,extra_pages+1))
	for x in range(1,extra_pages+1):
		getApps(x)


#this method will recieve an array of apps and will get the
# necessary info for each app and will then send the mails
def processApps(apps,gt = False):
	apps = apps['data']
	try:
		session = smtplib.SMTP('smtp.gmail.com',587) 
		session.ehlo()
		session.starttls()
		session.ehlo()
		session.login(sender,config.MAIL_PASS)

		for ap in apps:
			headersx={'access_token': token
			}

			#getting the op info
			op_r = requests.get("https://gis-api.aiesec.org/v2/opportunities/"+str(ap['opportunity']['id'])+".json", data=headersx)
			if op_r.status_code != 200:
				print 'another op '+str(op_r.status_code)
				op = None
			else:
				op = json.loads(op_r.text)
				#setManagerOp(manager_id =config.EXPA_USER_ID ,op = op)

			#getting the Ep info
			
			#ep_r = requests.get("https://gis-api.aiesec.org/v2/people/"+str(ap['person']['id'])+".json", data=headersx)
			ep_r = requests.get('https://gis-api.aiesec.org/v2/opportunities/'+str(op['id'])+'/applicant.json?person_id='+str(ap['person']['id'])+'&access_token='+ token)
			
			if ep_r.status_code != 200:
				print 'another ep '+str(ep_r.status_code)
				ep_r = requests.get("https://gis-api.aiesec.org/v2/people/"+str(ap['person']['id'])+".json", data=headersx)
				if ep_r.status_code != 200:
					print 'then again another ep'
					ep = None
				else:
					ep = json.loads(ep_r.text)
			else:
				ep = json.loads(ep_r.text)
				
			#getting the opp full
			#print op
			country = op['host_lc']['country'] if op['host_lc']['country'] != None else op['host_lc']['name']


			

			#checking if there's a CV
			cv = ''
			if ep != None and 'cv_info' in ep and ep['cv_info'] != None:
				cv = ep['cv_info']['url']

			if ep != None:
				sendMail(session,App(ap['person']['id'],ap['person']['email'],ap['person']['full_name'],
					ap['opportunity']['title'],ap['opportunity']['id'], cv
					,ep['managers'] if 'managers' in ep else '',op['managers'] if 'managers' in op else '',ap['url'], country))
			else:
				if (op != None):
					sendMail(session,App(ap['person']['id'],ap['person']['email'],ap['person']['full_name'],
						ap['opportunity']['title'],ap['opportunity']['id'], cv
						,'',op['managers'] if 'managers' in op else '',ap['url'], country))


		#
		session.quit()
	except smtplib.SMTPException as e:
		print e



#when there are multiple pages this method wil 
#recieve the number of page to request and then it will process all the apps
def getApps(page):
	headersx = headers
	headersx['page']=page
	r = requests.get("https://gis-api.aiesec.org/v2/applications.json", data=headersx)
	print 'PAGE '+str(page)
	message = json.loads(r.text)
	processApps(message)

	

#this method sents mail to ep managers and op manager
def sendMail(session,app):
	#self,ep_link,ep_mail,ep_name,op_name,op_link,cv_link,ep_managers,op_managers,app_link)
	#the lists for the mail involved with this app
	receivers = []
	to_epm =""
	to_opm =""
	#getting the EP managers and adding them to the mailing list for the mail
	for manager in app.ep_managers:
		receivers.append(manager['email'])
		to_epm+=manager["email"]+', '
	#getting the opportunity managers and adding them to the mailing list for the mail
	for manager in app.op_managers:
		if (manager['email'] not in  ['josem.martinezm@aiesec.net','noreply@aiesec.org.mx','dev.mexico@ai.aiesec.org']):
			receivers.append(manager['email'])
			to_opm+=manager["email"]+', '
	#msg['To'] = pay_data.ep_mail+','++',esuarez@aiesec.org.mx,jalanis@aiesec.org.mx' #pay_data.ep_mail
	m = """<h3>There's a new application in expa that you are managing</h3>
		EP name:	<a href='https://experience.aiesec.org/#/people/{}'>{} </a><br>
		EP mail:	{}<br>
		<a href='{}'>EP cv</a><br>
		EP managers:	{} <br>
		Opportunity:	<a href='https://experience.aiesec.org/#/opportunities/{}'>{}	</a><br>
		Opportunity Managers:	{}	<br><br><br>
		

		<h4>Please follow up to deliver a great experience</h4>
		""".format(app.ep_link , unicode(app.ep_name).encode('utf-8') , app.ep_mail , app.cv_link.encode('utf-8')  , to_epm , app.op_link,app.op_name.encode('utf-8') , to_opm ).encode('utf-8')
	msg = MIMEText(m,'html')
	
	msg['From'] = sender
	msg['bcc'] = to_opm+to_epm
	msg['Subject'] = '[AIESEC]New Application in EXPA {}({})-> {}({})'.format(unicode(app.ep_name).encode('utf-8'),app.ep_link,app.op_name.encode('utf-8'),app.op_link).encode('utf-8')
	
	try:
		#session.sendmail(sender,receivers,msg.as_string().encode('utf-8'))
		print app.country 
		if app.country != 'Mexico': #for all the opportunities that are not from mexico, ie, mexican EPs
			sendEPMail(session,app)
	except smtplib.SMTPException as e:
		print e

#this method sens mail to ep 
def sendEPMail(session,app):
	#self,ep_link,ep_mail,ep_name,op_name,op_link,cv_link,ep_managers,op_managers,app_link)
	#the lists for the mail involved with this app
	#receivers = [app.ep_mail]
	receivers = ['esuarez@aiesec.org.mx']
	to_epm =""
	to_opm =""
	# the reciever is the ep manager
	mail_ep = mail_html
	#getting the EP managers 
	for manager in app.ep_managers:
		to_epm+=manager["email"]+','
	#getting the opportunity managers and adding them to the mailing list for the mail
	for manager in app.op_managers:
		if (manager['email'] not in  ['josem.martinezm@aiesec.net','noreply@aiesec.org.mx','dev.mexico@ai.aiesec.org']):
			to_opm+=manager["email"]+'<br>'
	#msg['To'] = pay_data.ep_mail+','++',esuarez@aiesec.org.mx,jalanis@aiesec.org.mx' #pay_data.ep_mail
	m = """<h3>There's a new application in expa that you are managing</h3>
		EP name:	<a href='https://experience.aiesec.org/#/people/{}'>{} </a><br>
		EP mail:	{}<br>
		<a href='{}'>EP cv</a><br>
		EP managers:	{} <br>
		Opportunity:	<a href='https://experience.aiesec.org/#/opportunities/{}'>{}	</a><br>
		Opportunity Managers:	{}	<br><br><br>
		

		<h4>Please follow up to deliver a great experience</h4>
		""".format(app.ep_link , unicode(app.ep_name).encode('utf-8') , app.ep_mail , app.cv_link.encode('utf-8')  , to_epm , app.op_link,app.op_name.encode('utf-8') , to_opm ).encode('utf-8')


	ep_m = 	mail_ep.replace('{opportunity_name}',app.op_name).replace('{opportunity_country}',app.country).replace('{ep_managers}',to_epm).replace('{opportunity_mnagers}',to_opm).replace('{opportunity_link}',
		'https://opportunities.aiesec.org/opportunity/'+str(app.op_link))
	msg = MIMEText(unicode(ep_m).encode('utf-8'),'html')
	
	msg['From'] = sender
	msg['bcc'] = 'esuarez@aiesec.org.mx'
	msg['Subject'] = '[AIESEC]¡Felicidades por aplicar!'
	
	try:
		session.sendmail(sender,receivers,msg.as_string().encode('utf-8'))
	except smtplib.SMTPException as e:
		#print e
		return 
#this method gets  the content of  an opportunity as a jason and a person id and sets the person as manager for that op
def setManagerOp(manager_id, op):
	managers = []

	for m in op['managers']:
		managers.append(str(m['id']))
	#this means that the account is already a manager for this opp and nothing has to be done
	if str(manager_id) in managers:
		return

	mans=', '.join(managers)+','+str(manager_id)
	url = 'https://gis-api.aiesec.org/v2/opportunities/'+str(op['id'])+'.json?access_token='+token
	data = '{"opportunity":{"manager_ids":['+mans+']}}'
	requests.patch(url, data=data)	



#
#sendMail('Nombre de opp',10000,'jalanis@aiesec.org.mx','esuarez@aiesec.org.mx','Juanix')

#
#this call makes the whole notification deal happen
#uncoment to excecute notifications 
#the main method
def main():
	appNotificacion()	

# ejecucion 
if __name__ == "__main__":
	main()




