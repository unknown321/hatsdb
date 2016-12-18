function load_names() {
  text = $('#item_name').val()
  game_type = $('#game_type').val()
  if ((text.length >= 3)&&(game_type.length > 0)) {
    option = $($('#items').children('option')[0]).val()
    if (option != text){
      Dajaxice.mongobase.load_names_ajax(Dajax.process,{'text':text,'game_type':game_type})  
    }
  } else {
    $('#defindex').val('')
    $('#item_check i.fi-check.hidden').hide()
  }
}

function get_defitems(){
  $('#item_check i.fi-check.hidden').hide()
  text = $('#item_name').val()
  game_type = $('#game_type').val()
  if ((text.length >= 3)&&(game_type.length > 0)) {
      Dajaxice.mongobase.get_defitems_ajax(Dajax.process,{'text':text,'game_type':game_type});
  }
  $("[class='row defitems']").show()
  stickyFooter()
}

function second_step(item){
  $("#loaded_defitems").html('')
  $('#item_check i.fi-check.hidden').show()
  $("#item_name").val($(item).attr('name'))
  $("#defindex").val($(item).attr('defindex'))
  stickyFooter()
}

function load_team_names(team_number){
  $('#team'+team_number+'_check i.fi-check.hidden').hide()
  text = $('#team'+team_number+'_name').val()
  $('#team'+team_number).val('')
  game_type = $('#game_type').val()
  if ((text.length >= 3)&&(game_type.length > 0)) {
      Dajaxice.mongobase.get_team_names_ajax(Dajax.process,{'text':text,'game_type':game_type});
  }
  $("[class='row defitems']").show()
  stickyFooter()
}

function get_teams(team_number){
  $('#team'+team_number+'_check i.fi-check.hidden').hide()
  text = $('#team'+team_number+'_name').val()
  game_type = $('#game_type').val()
  if ((text.length >= 3)&&(game_type.length > 0)) {
      Dajaxice.mongobase.get_teams_ajax(Dajax.process,{'text':text,'game_type':game_type, 'team_number':team_number});
  }
  $("[class='row defitems']").show()
  stickyFooter()
}

function team_selected(team){
  $("#loaded_defitems").html('')
  $('#team'+$(team).attr('number')+'_check i.fi-check.hidden').show()
  $('#team'+$(team).attr('number')+'_name').val($(team).attr('name'))
  $('#team'+$(team).attr('number')).val($(team).attr('defindex'))
  stickyFooter()
}


function load_filtered_tourneys(page)
{
  $('#page').val(page)
  if (($("#item_name").val() === "") || ($("#item_name").val() === undefined))
    $("#defindex").val("")

  data = {}
  game_type = $('#game_type').val()
  data['game_type'] = $('#game_type').val()
  data['defindex'] = $("#defindex").val()
  data['page'] = $('#page').val()
  data['sort_by'] = $('input[name=sorttype]:checked').val()
  data['team1'] = $('#team1').val()
  data['team2'] = $('#team2').val()
  
  if (game_type == 'dota2'){
    data['player_sid'] = $('#player').val()
    data['match_id'] = $('#match_id').val()
    data['event_id'] = $('#event').multipleSelect('getSelects')
  }
  if (game_type == 'csgo'){
    data['event_type'] = $('#event_type').multipleSelect('getSelects')
    data['tournament'] = $('#tournament').multipleSelect('getSelects')
  }
  Dajaxice.mongobase.filter_tourneys_ajax(Dajax.process,{'data':data})  
}