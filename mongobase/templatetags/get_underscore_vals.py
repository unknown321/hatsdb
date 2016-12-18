from django import template
register = template.Library()

@register.filter(name='get')
def get(d, k):
    return d.get(k, None)

@register.filter(name='premium')
def premium(user_details, game_type):
	return user_details.is_premium(game_type)

@register.filter(name='multiply')
def multiply(value, arg):
    return value*arg

@register.filter(name='divide')
def divide(value, arg):
	val, remainder = divmod(value, arg)
	if remainder > 0:
		val += 1
	if val == 0 and remainder > 0:
		val = 1
	return val

@register.filter(name='trim')
def trim(value):
	a = str(value)
	if a.endswith('.0'):
		a = a[:-2]
	return a