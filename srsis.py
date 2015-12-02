from gevent import monkey
monkey.patch_all()

from flask import Flask, render_template
from flask.ext.socketio import SocketIO, emit

import xml.etree.ElementTree as ET
import requests

from ConfigParser import SafeConfigParser

from threading import Thread
import time

app = Flask(__name__)

parser = SafeConfigParser()
parser.read('config.ini')

app.config['SECRET_KEY'] = 'secretsecret'
app.config['SERVER_NAME'] = 'localhost:8080'

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

@socketio.on('connect', namespace='/test')
def test_connect():
	    emit('info', {'artist': getArtist(), 'title': getTitle(), 'listeners' : getListeners()})

def watch_thread():
	artist = getArtist()
	title = getTitle()
	listeners = getListeners()

	while True:
		time.sleep(2)

		rf_artist = getArtist()
		rf_title = getTitle()
		rf_listeners = getListeners()

		if (artist != rf_artist) or (title != rf_title) or (listeners != rf_listeners):

			print('detected false, emiting data')

			artist = rf_artist
			title = rf_title
			listeners = rf_listeners

			socketio.emit('info', {
					'artist': rf_artist,
					'title': rf_title,
					'listeners': rf_listeners
				})
		else:
			print('no changes found')

def get_tree():
	ice_user = parser.get('server', 'icecast_username')
	ice_pass = parser.get('server', 'icecast_password')
	ice_url = parser.get('server', 'xml_url')
	
	get = requests.get(ice_url, auth=(ice_user, ice_pass))

	if get.status_code != 200:
		raise Exception("status code %s" % get.status_code)
	else:
		return ET.ElementTree(ET.fromstring(get.text))

def getArtist():
	return unicode(get_tree().find(".//artist").text)

def getTitle():
	return unicode(get_tree().findall(".//title")[1].text)

def getListeners(): 
	return int(get_tree().find(".//listeners").text)

if __name__ == '__main__':
   socketio.run(app)