import conf
import csv
import os
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML


def query_yes_no(question):
    while True:
        answer = input(question)
        if answer in ['n', 'no', 'N']:
            return False
        if answer in ['y', 'yes', 'Y', None]:
            return True


def parse_niches(filename):
    niches = []
    with open(filename, mode='r') as file:
        for line in file.readlines():
            q, days = line.strip().split(';')
            query = {
                'q': q,
                'days': int(days)
            }
            niches.append(query)
    return niches


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

    _filename = filename + '.csv'
    with open(_filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(rows)

    print(f"CSV file '{filename}' created successfully.")


def render_html(niches, date_str):
    env = Environment(loader=FileSystemLoader('.'), cache_size=0)
    env.filters['intcomma'] = intcomma
    template = env.get_template('collection_result_template.html')
    this_folder = os.path.dirname(os.path.abspath(__file__))
    logo_path = 'file:\\' + os.path.join(this_folder, 'static', 'images', conf.logo_filename)
    return template.render(niches=niches, date_str=date_str, logo_path=logo_path)


def export_html(filename, niches, date_str):
    rendered_html = render_html(niches, date_str)
    _filename = filename + '.html'
    with open(_filename, 'w', encoding='utf-8') as f:
        f.write(rendered_html)
    print(f'HTML file {_filename} rendered successfully.')


def export_pdf(filename, niches, date_str):
    rendered_html = render_html(niches, date_str)
    _filename = filename + '.pdf'
    HTML(string=rendered_html).write_pdf(_filename)
    print(f'PDF file {_filename} created successfully.')
