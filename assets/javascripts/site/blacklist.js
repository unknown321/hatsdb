function switch_game(game, button)
{
  $('a.selected').removeClass('selected')
  $(button).addClass('selected')

  $('#game_type').val(game)
  $('#blacklist').val($('#blacklist_'+game).val())
  $('#bl_stuff').show()
  stickyFooter()
}

function load_names() {
	text = $('#lang').val()
	game_type = $('#game_type').val()
	if ((text.length >= 3)&&(game_type.length > 0)) {
		option = $($('#items').children('option')[0]).val()
		if (option != text){
			Dajaxice.mongobase.load_names_ajax(Dajax.process,{'text':text,'game_type':game_type})	
		}
		
	}
}

function add_item() {
	game_type = $('#game_type').val()
	if ($('#blacklist_'+game_type).val() == ''){
		$('#blacklist').val($('#blacklist').val() + $('#lang').val() + ';\n')	
	} else {
		$('#blacklist').val($('#blacklist').val() + ';\n' + $('#lang').val())
	}
	
}
function save_blacklist()
{	
	game_type = $("#game_type").val()
	blacklist_items = $('#blacklist').val()
	Dajaxice.mongobase.save_blacklist_ajax(Dajax.process,{'blacklist_items':blacklist_items,'game_type':game_type})
}

function load_default()
{	
	Dajaxice.mongobase.load_default_blacklist_ajax(Dajax.process,{'game_type':$("#game_type").val()})
}

function clear_blacklist()
{	
	$("#blacklist").val('')
}