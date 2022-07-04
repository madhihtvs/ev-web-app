function add() {
    var new_chq_no = parseInt($('#total_chq').val()) + 1;
    var new_input = "<input type='search' id='intermediate_point_" + new_chq_no + "' class='form-control rounded intermediate-btn' placeholder='Intermediate Point' style='display: table-cell; width: 100%; padding: 2%;'" + "name='intermediate_point_" + new_chq_no + "'>";
    $('#intermediate').append(new_input);
    $('#total_chq').val(new_chq_no)
}

function remove() {
    var last_chq_no = $('#total_chq').val();
    if (last_chq_no > 1) {
        $('#intermediate_point_' + last_chq_no).remove();
        $('#total_chq').val(last_chq_no - 1);
    }
}
