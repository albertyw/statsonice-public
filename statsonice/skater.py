from django.core.cache import cache
from django.http import Http404
from django.shortcuts import render, redirect
from time import time
from datetime import datetime
import json

from statsonice.models import Skater, SkaterTeam, Competitor, Program, SkaterResult
from statsonice.backend.profileresults import ProfileResults
from includes import unitconversion


# View to browse through all skaters
#
def browse(request):
    cache_key = 'skater_browse'
    response_dict = cache.get(cache_key)
    if not response_dict:
        skaters = {}
        for skater in Skater.objects.order_by('skatername__last_name'):
            url = skater.url()
            view_name = skater.view_name()
            skaters[skater.id] = [url, view_name, []]
        skater_teams = SkaterTeam.objects.all()
        for skater_team in skater_teams:
            url = skater_team.url()
            view_name = skater_team.view_name()
            skaters[skater_team.female_skater_id][2].append([url, view_name])
            skaters[skater_team.male_skater_id][2].append([url, view_name])
        skaters = skaters.values()
        skaters.sort(key=lambda i: i[1])
        response_dict = {'skaters':skaters}
        cache.set(cache_key, response_dict)
    return render(request, 'skater_browse.dj', response_dict)

# View to display information about a single skater
#
def profile(request, skater_first_name, skater_last_name):
    # Get skater
    try:
        skater = Skater.find_skater_by_url_name(skater_first_name, skater_last_name)
    except:
        raise Http404
    skater_name = skater.get_default_skater_name()
    skater_name.url_name_json = json.dumps(skater_name.url_name())

    # Redirect to canonical name (and url) if not default skater name
    if skater.url_name() != (skater_first_name, skater_last_name):
        return redirect(skater.url())

    # Compute skater information
    skater.height_feet, skater.height_inches = unitconversion.metric_to_imperial(skater.height)
    skater.other_names = list(skater.skatername_set.all())
    skater.other_names.remove(skater_name)

    # get results matrices
    profile_results = ProfileResults(skater)
    personal_records, best_total = profile_results.get_best_isu_programs()
    isu_results_matrix, isu_years = profile_results.get_isu_results_matrix()

    # get all results
    now = datetime.now()
    now = now.date()
    results = list(SkaterResult.objects.filter(competitor__skater=skater))
    results.sort(key=lambda x:x.competition.start_date)
    result_dic = {}
    for result in results:
        if result.competition.end_date > now:
            continue
        year = result.competition.start_date.year
        if year not in result_dic:
            result_dic[year] = []
        result_dic[year].append(result)

    result_dic = result_dic.items()
    result_dic.sort(key=lambda x:-x[0])


    return render(request, 'skater.dj', {
        'skater_name': skater_name,
        'skater': skater,
        'isu_results_matrix': isu_results_matrix,
        'isu_years': isu_years,
        'personal_records': personal_records,
        'best_total': best_total,
        'results': result_dic
    })

# View to display information about a skater team
#
def team_profile(request, first_skater_first_name, first_skater_last_name, second_skater_first_name, second_skater_last_name):
    try:
        first_skater = Skater.find_skater_by_url_name(first_skater_first_name, first_skater_last_name)
        second_skater = Skater.find_skater_by_url_name(second_skater_first_name, second_skater_last_name)
        skater_team = SkaterTeam.objects.get(female_skater=first_skater, male_skater=second_skater)
        competitor = Competitor.find_competitor(skater_team)
    except:
        raise Http404
    skater_team.url_name_json = json.dumps(first_skater.url_name()+second_skater.url_name())

    # skater heights
    first_skater.height_feet, first_skater.height_inches = unitconversion.metric_to_imperial(first_skater.height)
    second_skater.height_feet, second_skater.height_inches = unitconversion.metric_to_imperial(second_skater.height)

    # height gap
    if first_skater.height and second_skater.height:
        height_gap = second_skater.height - first_skater.height
        height_gap = list(unitconversion.metric_to_imperial(height_gap)) + [height_gap]
    else:
        height_gap = False

    # determine whether teams or dance
    program = Program.objects.filter(skater_result__competitor = competitor)
    if program.count() == 0:
        program = 0
        category = 0
    else:
        program = program[0]
        category = program.skater_result.category.category

    # get results matrices
    profile_results = ProfileResults(skater_team)
    personal_records, best_total = profile_results.get_best_isu_programs()
    isu_results_matrix, isu_years = profile_results.get_isu_results_matrix()

    # get all results
    now = datetime.now()
    now = now.date()
    results = list(SkaterResult.objects.filter(competitor__skater_team=skater_team))
    results.sort(key=lambda x:x.competition.start_date)
    result_dic = {}
    for result in results:
        if result.competition.end_date > now:
            continue
        year = result.competition.start_date.year
        if year not in result_dic:
            result_dic[year] = []
        result_dic[year].append(result)

    result_dic = result_dic.items()
    result_dic.sort(key=lambda x:-x[0])

    return render(request, 'skater_team.dj', {
            'first_skater': first_skater,
            'second_skater': second_skater,
            'height_gap': height_gap,
            'category': category,
            'skater_team': skater_team,
            'program': program,
            'isu_results_matrix': isu_results_matrix,
            'isu_years': isu_years,
            'personal_records': personal_records,
            'best_total': best_total,
            'results': result_dic
        })
