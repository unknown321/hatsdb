function switch_box(box,number)
  {
    var nums = [1,2,3]
    var index = nums.indexOf(number)
    nums.splice(index, 1)
    $('#' + box + '_' + number).attr('class',"radius label")
    $.each(nums,function(){$('#' + box + '_' + this).attr('class',"radius label secondary")})
    $('#' + box).val(number)
  }


function load_names() {
  text = $('#item_name').val()
  game_type = $('#game_type').val()
  if ((text.length >= 3)&&(game_type.length > 0)) {
    option = $($('#items').children('option')[0]).val()
    if (option != text){
      Dajaxice.mongobase.load_names_ajax(Dajax.process,{'text':text,'game_type':game_type})  
    }
  }
}

function get_defitems(){
  text = $('#item_name').val()
  game_type = $('#game_type').val()
  if ((text.length >= 3)&&(game_type.length > 0)) {
      Dajaxice.mongobase.get_defitems_ajax(Dajax.process,{'text':text,'game_type':game_type});
  }
  stickyFooter()
}

function load_stats(defindex, game_type){
  Dajaxice.mongobase.get_item_stats_ajax(Dajax.process,{'defindex':defindex,'game_type':game_type});
}

function second_step(item){
  $("#step2link").click()
  $("#noitem").hide()
  $("#hiddenstep2").show()
  $("#item_pic").attr('src',$(item).attr('img_url'))
  $("#item_name_ss").text($(item).attr('name'))
  $("#defindex").val($(item).attr('defindex'))

  load_stats($(item).attr('defindex'),$('#game_type').val())
  stickyFooter()
}

function get_values(){
  game_type = $('#game_type').val()
  data = {}
  if (game_type == 'tf2'){
    data['level'] = $('#level').val()
    data['craftnumber'] = $('#craftnumber').val()
    data['gifted'] = $("#gifted").prop('checked')
    data['effect'] = $('#effect').multipleSelect("getSelects")
    data['paint_id'] = $('#paint_id').multipleSelect("getSelects")
    data['ks_id'] = $('#ks_id').multipleSelect("getSelects")
    data['sheen_id'] = $('#sheen_id').multipleSelect("getSelects")
    data['ks_type'] = $('#ks_type').multipleSelect("getSelects")
    data['strange_parts'] = $('#strange_parts').multipleSelect("getSelects")
    data['item_uses'] = $('#item_uses').val()
  }
  if (game_type == 'dota2'){
    data['gems'] = $('#gems').multipleSelect("getSelects")
    data['gifted'] = $("#gifted").prop('checked')
    data['item_uses'] = $('#item_uses').val()
  }
  if (game_type == 'csgo'){
    data['exterior'] = $('#exterior').multipleSelect("getSelects")
    data['stickers'] = $('#stickers').multipleSelect("getSelects")
    data['gifted'] = $("#gifted").prop('checked')
    data['item_uses'] = $('#item_uses').val()
  }
  data['defindex'] = $('#defindex').val()
  data['game_type'] = game_type
  data['hours_more_than'] = $('#hours_more_than').val()
  data['hours_less_than'] = $('#hours_less_than').val()
  data['quality'] = $('#quality_id').multipleSelect("getSelects")
  data['craftable'] = $('#craftable').val()
  data['tradable'] = $('#tradable').val()
  return data
}

function load_search_results(page){
  var data = get_values()
  $('#page').val(page)
  data['page'] = $('#page').val()
  Dajaxice.mongobase.search_results_ajax(Dajax.process,{'data':data})
  $("#step3link").click()
}

function more_info(btn){
  $(btn).parent().parent().next().toggle()
}

function hide_info(btn){
  $(btn).parents('tr').toggle()
}