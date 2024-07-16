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


def discrepancy(rows, index):
    """
    Find channels with less than 50% the number of subscribers of its
    neighbours with comparable number of views.
    """
    rate = 2
    if len(rows) < 2:
        return []
    discrepancies = []
    # do first item
    if rows[0][index] < rows[1][index] * rate:
        discrepancies.append(0)
    for i in range(1, len(rows) - 2):
        if (rows[i][index] < rows[i-1][index] * rate or
           rows[i][index] < rows[i + 1][index] * rate):
            discrepancies.append(i)
    # do last item
    if rows[-1][index] < rows[-2][index] * rate:
        discrepancies.append(len(rows) - 1)
    return discrepancies


def export_csv(filename, header, rows):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(rows)

    print(f"CSV file '{filename}' created successfully.")


def render_html(niches, date_str):
    env = Environment(loader=FileSystemLoader('.'), cache_size=0)
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
