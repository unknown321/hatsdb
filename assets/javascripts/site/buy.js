function buy(game_type) {
  Dajaxice.mongobase.buy_ajax(Dajax.process,{'game_type':game_type})  
}