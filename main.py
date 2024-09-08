import time
import requests


# Miscellaneous scripts for assorted purposes
#
# meetme_active_viewers: Prints how many viewers are currently active in a Meetme stream.

def meetme_active_viewers():
    email = input('Enter email: ')
    password = input('Enter password: ')

    login_response = login(email, password)
    xsrf = login_response.json()['requestToken']

    auth = get_auth(xsrf)
    access_token = auth.json()["access_token"]
    me_pyl = {'_ApplicationId': 'sns-video',
              '_ClientVersion': 'js3.4.4',
              '_InstallationId': '',  # de7e5ad7-06d4-43e5-9404-7f1908734413
              '_method': 'GET',
              '_SessionToken': f'{access_token}'}  # from /oauth/token call
    # grab session token
    me_url = 'https://api.gateway.meetme.com/video-api/meetme/users/me'
    me_response = session.post(url=me_url, json=me_pyl, headers={'Content-Type': 'text/plain'})
    session_token = me_response.json()['sessionToken']

    live_favs = get_favs_live(session_token)
    broadcast_id = input("Submit desired broadcastID: ")
    leave_live = False

    while broadcast_id.lower() != 'exit':
        viewer_id = view_broadcast(broadcast_id, session_token, 'following').json()
        print(f'Joined live broadcast (id: {broadcast_id})')
        print('Available commands: leave, like, grabviews')
        while not leave_live:
            command = input('Submit command: ').lower()
            if command == 'leave':
                leave_live = True
                break
            elif command == 'like':
                likes = int(input('Enter amount of likes to send: '))
                if likes > 30:
                    likes_mp = likes/30
                    likes_rem = likes%30
                    likes_count = 0
                    while likes_count < likes:
                        send_hearts(broadcast_id, session_token, 30, viewer_id)
                        likes_count += 30
                        time.sleep(0.5)
                    if likes_rem != 0:
                        send_hearts(broadcast_id, session_token, likes_rem, viewer_id)
                else:
                    send_hearts(broadcast_id, session_token, likes, viewer_id)
            elif command == 'grabviews':
                get_broadcast_viewer_count(broadcast_id, access_token)

        broadcast_id = input("Submit desired broadcastID: ")

    print('Program terminated')


def login(login_user, login_pass):
    #   test_url = 'https://httpbin.org/post'
    # Login Info
    url = 'https://ssl.meetme.com/mobile/login'
    payload = {'emailId': f'{login_user}', 'password': f'{login_pass}'}
    headers = {'x-device': 'phoenix/screen_medium,c9fd2958-3a2c-45de-abdb-522c3af370e2,5.46.2'}
    # Login Requests / Responses
    options = session.options(url=url)
    response = session.post(url=url, headers=headers, data=payload)

    if 'error' in response.json():
        raise Exception(f'A Login error occurred: {response.json()["errorCode"]} {response.json()["errorType"]}. '
                        f'Username / password combination may be incorrect.')
    else:
        print(f'Logged in as {response.json()["member"]["first_name"]} (ID: {response.json()["member"]["member_id"]})')

    return response


def get_auth(xsrf):
    oauth_headers = {'xsrf': f'{xsrf}',
                     'x-device': 'phoenix/screen_medium,c9fd2958-3a2c-45de-abdb-522c3af370e2,5.46.2'}
    oauth_identifier = session.get(url='https://ssl.meetme.com/mobile/oauthIdentifier', headers=oauth_headers)
    subject_token = oauth_identifier.json()['token']
    auth_pyl = {'grant_type': 'urn:ietf:params:oauth:grant-type:token-exchange',
                'subject_token': f'{subject_token}',
                'subject_token_type': 'urn:ietf:params:oauth:token-type:session'}
    auth_head = {'Authorization': 'Basic bWVldG1lOnNlY3JldA==',
                 'Content-Type': 'application/x-www-form-urlencoded'}
    return session.post(url='https://auth.gateway.meetme.com/oauth/token', headers=auth_head, data=auth_pyl)


def get_favs():
    # WIP, need session token from /video-api/meetme/users/me
    following_pyl = {'pageSize': '20', 'score': '0', 'type': 'SNSVideo'}
    following_url = 'https://api.gateway.meetme.com/video-api/meetme/functions/sns-follow:getFollowingWithUserDetails'
    following_response = session.post(url=following_url, data=following_pyl)


def get_favs_live(session_token):
    url = 'https://api.gateway.meetme.com/video-api/meetme/functions/sns-video:getFollowingBroadcasts'
    # An interesting bug observed: if User-Agent is set to python (default) there will be 21 additional streamers
    # returned, even though those streamers are not followed. These additional broadcasts appear to be pulled from
    # trending.
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0',
               'X-Parse-Application-Id': 'sns-video',
               'X-Parse-Session-Token': f'{session_token}'}
    payload = {'pageSize': 20,
               'gender': "all",
               'latitude': 47.6115,
               'longitude': -122.3343,
               'score': "0"}

    live_favs_data = session.post(url=url, headers=headers, json=payload)
    following = live_favs_data.json()['result']

    print(f'There are {following["score"]} followed streamers live:')
    count = 0
    for i in following['broadcasts']:
        count += 1
        print(f'{count}.\t{i["objectId"]}\t {i["userDetails"]["firstName"]}')

    return live_favs_data


def get_trending_live(session_token, count):
    url = 'https://api.gateway.meetme.com/video-api/meetme/functions/sns-video:getTrendingBroadcasts'
    headers = {'Content-Type': 'application/json; charset=utf-8',
               'X-Parse-Application-Id': 'sns-video',
               'X-Parse-Session-Token': f'{session_token}'}
    payload = {'gender': 'all',
               'latitude': 47.6115,
               'longitude': -122.3343,
               'pageSize': count,
               'score': '0'}

    return session.post(url=url, headers=headers, json=payload)


def get_broadcast_metadata(broadcast_id, session_token):
    url = f'https://api.gateway.meetme.com/video-metadata/broadcast/{broadcast_id}'
    headers = {'Content-Type': 'application/json; charset=utf-8',
               'X-Parse-Application-Id': 'sns-video',
               'Authorization': f'Bearer {session_token}'}

    metadata = session.get(url=url, headers=headers)
    metadata = metadata.json()
    return metadata


def get_broadcast_viewer_count(broadcast_id, session_token):
    metadata = get_broadcast_metadata(broadcast_id, session_token)
    active_viewers = metadata['broadcast']['result']['currentViewers']
    total_viewers = metadata['broadcast']['result']['totalViewers']
    print(f'{active_viewers} / {total_viewers} viewers active')


def send_hearts(broadcast_id, session_token, num_hearts, viewer_id):
    if num_hearts > 30:
        print('Likes cannot be greater than 30')
        num_hearts = 30

    url = 'https://api.gateway.meetme.com/video-api/meetme/functions/sns-video:likeBroadcast'
    headers = {'Content-Type': 'application/json; charset=utf-8',
               'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0',
               'X-Parse-Session-Token': f'{session_token}',
               'X-Parse-Application-Id': 'sns-video'}
    payload = {'broadcastId': f'{broadcast_id}',
               'numLikes': int(num_hearts),
               'viewerId': f'{viewer_id}'}

    likes = session.post(url=url, headers=headers, json=payload)

    if likes.status_code != 200:
        raise Exception(f'Unable to send likes, status code {likes.status_code}')

    #print(f'Sent {num_hearts} to streamer')


def view_broadcast(broadcast_id, session_token, source):
    url = 'https://api.gateway.meetme.com/video-api/meetme/functions/sns-video:viewBroadcast'
    headers = {'Content-Type': 'application/json; charset=utf-8',
               'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0',
               'X-Parse-Session-Token': f'{session_token}',
               'X-Parse-Application-Id': 'sns-video'}
    payload = {'broadcastId': f'{broadcast_id}',
               'source': f'{source}',
               'viewBroadcast': True}

    return session.post(url=url, headers=headers, json=payload)


def get_member_settings(login_token):
    member_settings_url = 'https://profile.meetme.com/mobile/membersettings'
    member_settings_header = {'x-device': 'phoenix/screen_medium,c9fd2958-3a2c-45de-abdb-522c3af370e2,5.46.2',
                              'xsrf': f'{login_token}'}
    return session.get(url=member_settings_url, headers=member_settings_header)


if __name__ == '__main__':
    session = requests.Session()
    meetme_active_viewers()
