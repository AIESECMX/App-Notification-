#The purpose of this script is to get a token for the operations with the 
#AIESEC platform EXPA the methods here allow you to get e token for EXPA and for YOP
#Author: Enriqe Suarez MCVP Data Intelligence AIESEC in Mexico
#Version: 1.2
#Last update: March 21, 2017s
#
#Usage :
#simpple usage request ofr the method that will get the token either from EXPA dn YOP with
#User mail and password as parameters and will get the the plain text token as a return statetment
#
import urllib
import urllib2
import cookielib
import logging
import datetime
import json
from bs4 import BeautifulSoup


class GIS:
    
    def __init__(self):
        self.cj = cookielib.CookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
        
        

    def generate_token(self,email,password):
        
        succes = False
        attempts = 0
        #asking to be redirected to YOP intead of EXPA
        url='https://auth.aiesec.org/oauth/authorize?redirect_uri=https%3A%2F%2Fexperience.aiesec.org%2Fsign_in&response_type=code&client_id=349321fd15814e9fdd2c5abe062a6fb10a27a95dd226fce287adb6c51d3de3df'
        # create the request 
        req = urllib2.Request(url)
        #try 3 times
        while not succes and attempts < 3:
            #being redirected to YOP
            res = self.opener.open(req)
            if res:
                succes = True
            #
            attempts +=1
        #if we were redirected to YOp then que request for the YOP Token
        
        if succes :
            url = 'https://auth.aiesec.org/users/sign_in'
            req = urllib2.Request(url)
            res = self.opener.open(req)
            soup3 = BeautifulSoup(res.read(),'html.parser')
            desc = soup3.findAll('meta') 
            auth_token = (desc[1]['content'].encode('utf-8'))
            login_data = urllib.urlencode({'user[email]': email, 'user[password]': password,'authenticity_token':auth_token,'commit':'Sign in'})

            #login_data = urllib.urlencode({'user[email]': email, 'user[password]': password})
            #logging.info('Generating a token for {0}...'.format(self.email))
            self.opener.open('https://auth.aiesec.org/users/sign_in', login_data)
            token = None
            for cookie in self.cj:
                if cookie.name == 'expa_token':
                    token = cookie.value
            if token is None:
                raise Exception('Unable to generate a token for {0}!'.format(email))
            return token
        else:
            print 'no cookie found'




    #
    def generate_op_token(self,email,password):
        succes = False
        attempts = 0
        #asking to be redirected to YOP intead of EXPA
        url='https://auth.aiesec.org/oauth/authorize?redirect_uri=https%3A%2F%2Fopportunities.aiesec.org%2Fauth&response_type=code&client_id=e34d5daf8c89172f7fabccbae8378eb3cb524cffc774c57afe2011b90d2e77e5'
        # create the request 
        req = urllib2.Request(url)
        #try 3 times
        while not succes and attempts < 3:
            #being redirected to YOP
            res = self.opener.open(req)
            if res:
                succes = True
            #
            attempts +=1
        #if we were redirected to YOp then que request for the YOP Token
        if succes :
            url = 'https://auth.aiesec.org/users/sign_in'
            req = urllib2.Request(url)
            res = self.opener.open(req)
            soup3 = BeautifulSoup(res.read(),'html.parser')
            desc = soup3.findAll('meta') 
            auth_token = (desc[1]['content'].encode('utf-8'))
            login_data = urllib.urlencode({'user[email]': email, 'user[password]': password,'authenticity_token':auth_token,'commit':'Sign in'})

            #login_data = urllib.urlencode({'user[email]': email, 'user[password]': password})
            #logging.info('Generating a token for {0}...'.format(self.email))
            self.opener.open('https://auth.aiesec.org/users/sign_in', login_data)
            token = None
            for cookie in self.cj:
                if cookie.name == 'aiesec_token':
                    
                    token = json.loads(urllib.unquote(cookie.value).decode('utf8'))['token']['access_token']
            if token is None:
                raise Exception('Unable to generate a token for {0}!'.format(email))
            return token
        else:
            print 'error para hacer el sign in a YOP'



