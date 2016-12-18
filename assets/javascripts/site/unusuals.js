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
    $('i.fi-check.hidden').hide()
  }
}

function get_defitems(){
  $('i.fi-check.hidden').hide()
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
  $('i.fi-check.hidden').show()
  $("#item_name").val($(item).attr('name'))
  $("#defindex").val($(item).attr('defindex'))
  stickyFooter()
}

function load_filtered_unusuals(page)
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
  if (game_type == 'tf2'){
    data['level'] = $('#level').val()
    data['effect'] = $('#effect').multipleSelect("getSelects")
  }
  if (game_type == 'dota2'){
    data['gems'] = $('#effect').multipleSelect("getSelects")
  }
  if (game_type == 'csgo'){
    data['quality'] = $('#quality_id').multipleSelect('getSelects')
    data['exterior'] = $('#exterior_id').multipleSelect('getSelects')
  }
  Dajaxice.mongobase.filter_unusuals_ajax(Dajax.process,{'data':data})  
}