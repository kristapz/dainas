$(function() {
	$('#chars').change(function() {
		var field = $(this).attr('value');
		var search_text = $('#searchText').attr('value') ? $('#searchText').attr('value') : '';
		$('#searchText').attr('value', search_text+field);
		
	});
});