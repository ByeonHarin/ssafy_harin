# -*- coding: utf-8 -*-
import json
import os
import re
import urllib.request
from operator import eq
from bs4 import BeautifulSoup

from bs4 import BeautifulSoup
from slackclient import SlackClient
from flask import Flask, request, make_response, render_template

app = Flask(__name__)
slack_token = "xoxb-506472500310-507380090067-KUVlmF8E3xSDZyS7T6aNXS1d"
slack_client_id = "506472500310.507315119380"
slack_client_secret = "2ce0c6644931dbba21a4da3a45fbd086"
slack_verification = "zTWYxTQBAXTCnSuCti46xeFR"
sc = SlackClient(slack_token)

# 크롤링 함수 구현하기



def _crawl_portal_keywords(text):
    # 여기에 함수를 구현해봅시다.
    genre = ""
    temp = text.split()[1] + " " + text.split()[2]
    print(type(temp))
    if "인디" in temp:
        genre = "인디"
        url = "https://music.bugs.co.kr/genre/chart/kpop/indie/total/day"
    elif "발라드" in temp:
        genre = "발라드 댄스 팝"
        url = "https://music.bugs.co.kr/genre/chart/kpop/ballad/total/day"
    elif "랩" in temp:
        genre = "랩 힙합"
        url = "https://music.bugs.co.kr/genre/chart/kpop/rnh/total/day"
    elif "락" in temp:
        genre = "락 메탈"
        url = "https://music.bugs.co.kr/genre/chart/kpop/rock/total/day"
    elif "성인가요" in temp:
        genre = "성인가요"
        url = "https://music.bugs.co.kr/genre/chart/kpop/adultkpop/total/day"
    elif "소울" in temp:
        genre = "소울 알앤비"
        url = "https://music.bugs.co.kr/genre/chart/kpop/rns/total/day"
    elif "인기차트" in temp:
        genre = "인기차트"
        url = "https://music.bugs.co.kr/"

    sourcecode = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(sourcecode, "html.parser")
    keyret = []
    keywords = []
    keyartists = []
    count = 1


    if ("리스트" in temp) and eq(genre, "인기차트"):
        for data in (soup.find_all("div", class_="chartContainer")):
            for i in (data.find_all("p", class_="artist")):
                if not i.get_text() in keyartists:
                    keyartists.append(i.get_text().replace('\n', ''))
            for i in (data.find_all("p", class_="title")):
                if not i.get_text() in keywords:
                    if count <= 10:
                        ss = (str(count) + "위: ".replace('\n', '') + i.get_text().replace('\n', '') + " / " + keyartists[count - 1])
                        keywords.append(ss)
                        count += 1
                    else:
                        break
    if ("듣고싶어" in temp) and eq(genre, "인기차트"):
        for data in (soup.find_all("div", class_="chartContainer")):
            for i in (data.find_all("p", class_="title")):
                if not i.get_text() in keywords:
                    if count <= 10:
                        keywords.append(i.get_text().replace('\n', ''))
                        count += 1
                    else:
                        break
        for i in range(2):
            keyret.append(_youtube_loader(keywords[i]))
        return u'\n'.join(keyret)
    if ("리스트" in temp) and not eq(genre, "인기차트"):
        for data in (soup.find_all("div", class_="innerContainer")):
            for i in (data.find_all("p", class_="artist")):
                if not i.get_text() in keyartists:
                    keyartists.append(i.get_text().replace('\n', ''))
            for i in (data.find_all("p", class_="title")):
                if not i.get_text() in keywords:
                    if count <= 10:
                        ss = (str(count) + "위: ".replace('\n', '') + i.get_text().replace('\n', '') + " / " + keyartists[count - 1])
                        keywords.append(ss)
                        count += 1
                    else:
                        break
    if ("듣고싶어" in temp) and not eq(genre, "인기차트"):
        for data in (soup.find_all("div", class_="innerContainer")):
            for i in (data.find_all("p", class_="title")):
                if not i.get_text() in keywords:
                    if count <= 10:
                        keywords.append(i.get_text().replace('\n', ''))
                        count += 1
                    else:
                        break
        for i in range(2):
            keyret.append(_youtube_loader(keywords[i]))
        return u'\n'.join(keyret)


    # 한글 지원을 위해 앞에 unicode u를 붙혀준다.
    return u'\n'.join(keywords)

#api 안쓰고 읽어오는 코드 (이 함수 자주돌리면 밴당함)


def _youtube_loader(text):

    textToSearch = text
    query = urllib.parse.quote(textToSearch)
    url = "https://www.youtube.com/results?search_query=" + query
    response = urllib.request.urlopen(url)
    html = response.read()
    soup = BeautifulSoup(html, 'html.parser')
    keywords = []
    for vid in soup.findAll(attrs={'class':'yt-uix-tile-link'}):
        keywords.append('https://www.youtube.com' + vid['href'])
        break
    # 한글 지원을 위해 앞에 unicode u를 붙혀준다.
    return u'\n'.join(keywords)


# 이벤트 핸들하는 함수
def _event_handler(event_type, slack_event):
    print(slack_event["event"])

    if event_type == "app_mention":
        channel = slack_event["event"]["channel"]
        text = slack_event["event"]["text"]

        keywords = _crawl_portal_keywords(text)
        sc.api_call(
            "chat.postMessage",
            channel=channel,
            text=keywords
        )

        return make_response("App mention message has been sent", 200,)

    # ============= Event Type Not Found! ============= #
    # If the event_type does not have a handler
    message = "You have not added an event handler for the %s" % event_type
    # Return a helpful error message
    return make_response(message, 200, {"X-Slack-No-Retry": 1})


@app.route("/listening", methods=["GET", "POST"])
def hears():
    slack_event = json.loads(request.data)

    if "challenge" in slack_event:
        return make_response(slack_event["challenge"], 200, {"content_type":
                                                                 "application/json"
                                                             })

    if slack_verification != slack_event.get("token"):
        message = "Invalid Slack verification token: %s" % (slack_event["token"])
        make_response(message, 403, {"X-Slack-No-Retry": 1})

    if "event" in slack_event:
        event_type = slack_event["event"]["type"]
        return _event_handler(event_type, slack_event)

    # If our bot hears things that are not events we've subscribed to,
    # send a quirky but helpful error response
    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
                         you're looking for.", 404, {"X-Slack-No-Retry": 1})


@app.route("/", methods=["GET"])
def index():
    return "<h1>Server is ready.</h1>"


if __name__ == '__main__':
    app.run('127.0.0.1', port=5000)
