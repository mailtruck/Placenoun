import random

from decimal import Decimal, getcontext

from django.shortcuts import render_to_response
from django.template import RequestContext

from placenoun.pn.models import NounStatic, NounExternal, SearchGoogle, SearchBing

def index(request):
  template = 'index.html'
  data = {}

  context = RequestContext(request)
  return render_to_response(template, data, context)

def noun_static(request, noun, width, height):
  width = min(2048, int(width))
  height = min(2048, int(height))

  noun_query = NounStatic.objects.filter(noun = noun, width = width, height = height)[:1]
  if noun_query:
    this_image = noun_query.get()
    return this_image.http_image

  noun_query = NounExternal.objects.filter(available = True, noun = noun, width = width, height = height)[:1]
  if noun_query:
    this_image = noun_query.get()
    if this_image.id:
      this_image = this_image.to_static()
      return this_image.http_image

  num_part = str(Decimal(width)/Decimal(height)).split('.')[0]
  getcontext().prec = len(num_part) + 10
  aspect = Decimal(width)/Decimal(height)
  noun_query = NounExternal.objects.filter(available = True, noun= noun, aspect = aspect, width__gte = width, height__gte = height)[:1]
  q2 = noun_query
  if noun_query:
    this_image = noun_query.get()
    if this_image.id:
      this_image = this_image.to_static(size=(width, height))
      return this_image.http_image


  # At this point we couldn't find a suitable match, so... we'll serve
  # up a best fit result but it won't be perminant

  random.choice([SearchBing, SearchGoogle]).do_next_search(noun)

  radius = 1
  while True:
    noun_query = NounExternal.objects.filter(noun = noun).filter(
      width__lte = width + radius, height__lte = height + radius).filter(
      width__gte = width - radius, height__gte = height - radius)[:100]
    if not noun_query:
      radius = radius*2
      if radius > 2000:
        random.choice([SearchBing, SearchGoogle]).do_next_search(noun)
        radius = 1
      continue
    noun_query = sorted(noun_query, key = lambda noun_obj: ( (width-noun_obj.width)**2 + (height-noun_obj.height)**2)**0.5 )[:1]
    this_image = noun_query[0]
    if not this_image.id:
      continue
    return this_image.http_image_resized(size=(width, height))

def noun(request, noun):
  noun_query = NounExternal.objects.filter(noun = noun).order_by('?')[:1]
  if noun_query:
    this_image = noun_query.get()
    if this_image.id:
      return this_image.http_image

  random.choice([SearchBing, SearchGoogle]).do_next_search(noun)

  while True:
    noun_query = NounExternal.objects.filter(noun = noun).order_by('?')[:1]
    if noun_query:
      this_image = noun_query.get()
      if not this_image.id:
        continue
      return this_image.http_image
