from gevent import monkey
monkey.patch_all()

from flask import Flask, render_template
from flask.ext.socketio import SocketIO, emit

from xml.dom import minidom
import requests

from ConfigParser import SafeConfigParser

from threading import Thread
import time

app = Flask(__name__)

parser = SafeConfigParser()
parser.read('config.ini')

app.config['SECRET_KEY'] = 'secretsecret'

socketio = SocketIO(app)
thread = None

# MAIN PAGES
@app.route('/')
def root():
	global thread

	if thread is None:
		thread = Thread(target = watch_thread)
		thread.start()

	return render_template('index.html')

def watch_thread():
	while True:
		artist = getArtist()
		title = getTitle()
		listeners = getListeners()

		time.sleep(2)

		rf_artist = getArtist()
		rf_title = getTitle()
		rf_listeners = getListeners()

		if (artist != rf_artist) or (title != rf_title) or (listeners != rf_listeners):
			print('detected false, emiting data')

			socketio.emit('info', {
					'artist': rf_artist,
					'title': rf_title,
					'listeners': rf_listeners
				})

def fetch_XML():
	ice_user = parser.get('server', 'icecast_username')
	ice_pass = parser.get('server', 'icecast_password')
	ice_url = parser.get('server', 'xml_url')
	
	get = requests.get(ice_url, auth=(ice_user, ice_pass))
	return minidom.parseString(get.text)

def getArtist():
	return unicode(fetch_XML().getElementsByTagName('artist')[0].firstChild.data)

def getTitle():
	return unicode(fetch_XML().getElementsByTagName('title')[1].firstChild.data)

def getListeners(): 
	return int(fetch_XML().getElementsByTagName('listeners')[0].firstChild.data)

if __name__ == '__main__':
   socketio.run(app)