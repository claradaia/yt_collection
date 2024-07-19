import ast
import conf
import csv
import os
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from openai import OpenAI
from iso3166 import countries
from datetime import datetime
from googleapiclient.discovery import build
import webbrowser


# configure yt access
youtube = build('youtube', 'v3', developerKey=conf.YT_API_KEY)


def query_yes_no(question, default='no'):
    while True:
        answer = input(question)
        if answer == '':
            answer = default
        if answer in ['n', 'no', 'N']:
            return False
        if answer in ['y', 'yes', 'Y']:
            return True


def parse_niches(filename):
    niches = []
    with open(filename, mode='r') as file:
        for line in file.readlines():
            q, days, max_sub = line.strip().split(';')
            query = {
                'q': q,
                'days': int(days),
                'max_subscribers': int(max_sub)
            }
            niches.append(query)
    return niches


def get_title_suggestions(niche):
    client = OpenAI(api_key=conf.OPENAI_API_KEY)

    response = client.chat.completions.create(
      model="gpt-3.5-turbo",
      messages=[
        {
          "role": "system",
          "content": [
            {
              "type": "text",
              "text": "You are a famous youtuber that also knows programming. You will be provided with a topic, "
                      "and your task is to print 10 suggested YouTube video names as a python list variable without "
                      "any headers or extra formatting."
            }
          ]
        },
        {
          "role": "user",
          "content": [
            {
              "type": "text",
              "text": niche
            }
          ]
        }
      ],
      temperature=1,
      max_tokens=256,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0
    )
    try:
        titles = ast.literal_eval(response.choices[0].message.content)
    except:
        _filename = niche.replace(' ', '_') + ".txt"
        with open(_filename, "w", encoding='utf-8') as file:
            file.write(response.choices[0].message.content)
        print(f'Something went wrong with OpenAI response for niche \"{niche}\". '
              f'The output has been saved to \"{niche}.txt\" for reference.')
        return []
    return titles


def discrepancy(videos):
    """
    Find channels with less than 50% the number of subscribers of its
    neighbours with comparable number of views.
    """
    rate = 2
    if len(videos) < 2:
        return True

    # do first item
    if videos[0]['channel']['subscribers'] * rate < videos[1]['channel']['subscribers']:
        videos[0]['discrepancy'] = True
    for i in range(1, len(videos) - 2):
        if (videos[i]['channel']['subscribers'] * rate < videos[i-1]['channel']['subscribers'] or
           videos[i]['channel']['subscribers'] * rate < videos[i+1]['channel']['subscribers']):
            videos[i]['discrepancy'] = True
    # do last item
    if videos[-1]['channel']['subscribers'] * rate < videos[-2]['channel']['subscribers']:
        videos[-1]['discrepancy'] = True

    return True


def intcomma(value):
    return "{:,}".format(int(value))


def export_csv(filename, niches, date_str):
    header = [
        'Niche',
        'Video URL',
        'Video Title',
        'Release Date',
        'Views Count',
        'Channel Title',
        'Channel Subscribers',
        'Channel Views',
        'Country',
        'Collection Date'
    ]

    rows = []
    for niche in niches:
        row = [niche['q']]  # niche
        for video in niche['videos']:
            row.extend([
                video['id'],
                video['title'],
                video['release_date'],
                video['views'],
                video['channel']['title'],
                video['channel']['subscribers'],
                video['channel']['views'],
                video['channel']['country'],
                date_str
            ])
            rows.append(row)

    _filename = os.path.join(conf.OUTPUT_DIR, filename + '.csv')
    with open(_filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(rows)

    print(f"CSV file '{_filename}' created successfully.")


def render_html(niches, date_str):
    env = Environment(loader=FileSystemLoader('.'), cache_size=0)
    env.filters['intcomma'] = intcomma
    template = env.get_template('collection_result_template.html')
    this_folder = os.path.dirname(os.path.abspath(__file__))
    logo_path = 'file:\\' + os.path.join(this_folder, 'static', 'images', conf.logo_filename)
    return template.render(niches=niches, date_str=date_str, logo_path=logo_path)


def export_html(filename, niches, date_str):
    rendered_html = render_html(niches, date_str)
    _filename = os.path.join(conf.OUTPUT_DIR, filename + '.html')
    with open(_filename, 'w', encoding='utf-8') as f:
        f.write(rendered_html)
    print(f'HTML file {_filename} rendered successfully.')


def export_pdf(filename, niches, date_str):
    rendered_html = render_html(niches, date_str)
    _filename = os.path.join(conf.OUTPUT_DIR, filename + '.pdf')
    HTML(string=rendered_html).write_pdf(_filename)
    print(f'PDF file {_filename} created successfully.')


def search_videos(q, date_cutoff=None, max_pages=3, max_videos=20, max_subscribers=None):
    p = 0
    next_page = True
    page_token = None

    channels = {}
    formatted_videos = []

    while p < max_pages and next_page and len(formatted_videos) < max_videos:
        search_response = youtube.search().list(
            part='snippet',
            q=q,
            type='video',
            publishedAfter=date_cutoff,
            order='viewCount',
            pageToken=page_token,
            maxResults=50
        ).execute()

        videos_found_r = search_response['items']

        # get ids to request details
        video_ids = []
        channel_ids = []  # only the ones not queried yet
        for video in videos_found_r:
            video_ids.append(video['id']['videoId'])
            if video['snippet']['channelId'] not in channels:
                channel_ids.append(video['snippet']['channelId'])

        channels_response = youtube.channels().list(
            id=','.join(channel_ids),
            part='snippet,statistics'
        ).execute()

        channels_r = channels_response['items']

        for item in channels_r:
            country_code = item['snippet'].get('country')
            country = countries.get(country_code).name if country_code else 'Not Available'
            channel = {
                'title': item['snippet']['title'],
                'subscribers': int(item['statistics']['subscriberCount']),
                'views': item['statistics']['viewCount'],
                'country': country
            }
            channels[item['id']] = channel

        videos_details_r = youtube.videos().list(
            id=','.join(video_ids),
            part='snippet,statistics'
        ).execute()['items']

        # drop if channel has more than the max subscribers
        previous_len = len(videos_details_r)
        videos_details = [item for item in videos_details_r if channels[item['snippet']['channelId']]['subscribers'] <= int(max_subscribers)]
        print(f'Page {p + 1}: {previous_len - len(videos_details)} videos dropped for having more subscribers than '
              f'the limit.')

        # format and join
        for video in videos_details:
            release_date = datetime.strptime(video['snippet']['publishedAt'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')

            video_item = {
                'id': video['id'],
                'title': video['snippet']['title'],
                'release_date': release_date,
                'views': video['statistics']['viewCount'],
                'channel': channels[video['snippet']['channelId']],
                'discrepancy': False
            }
            formatted_videos.append(video_item)

        # pagination stuff
        page_token = search_response.get('nextPageToken')
        if not page_token:
            next_page = False
        p += 1

    if not next_page:
        reason = 'No more pages to retrieve.'
    elif len(formatted_videos) >= max_videos:
        reason = 'Reached max videos.'
    else:  # p == max_pages
        reason = 'Reached max requests quota.'

    if len(formatted_videos) > max_videos:
        formatted_videos = formatted_videos[:max_videos]

    plural = 's' if p > 1 else ''
    print(f'{reason}\n'
          f'{p} page{plural} retrieved.\n'
          f'{len(formatted_videos)} videos collected.')

    return formatted_videos


def manual_check(videos):
    print(f'Starting manual check with {len(videos)}...')
    for video in videos:
        # open browser
        url = f"https://www.youtube.com/watch?v={video['id']}"
        webbrowser.open(url)

        if not query_yes_no(f"\n\"{video['title']}\" --- Include? [Y/n]:", default='yes'):
            videos.remove(video)
    print(f'Videos left after manual check: {len(videos)}')
