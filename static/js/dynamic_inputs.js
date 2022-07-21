function add() {
    var new_chq_no = parseInt($("#total_chq").val()) + 1;
    var new_input = `<div id='intermediate_point_${new_chq_no}_parent'  class="autocomplete-container">
                        
                    </div>`;
    $("#intermediate").append(new_input);
    $("#total_chq").val(new_chq_no);

    autoCompleteAddress(
        document.getElementById(`intermediate_point_${new_chq_no}_parent`),
        `intermediate_point_${new_chq_no}`,
        "Enter Intermediate Point",
        (data) => {
            payload["orig_lon"] = data["geometry"]["coordinates"][0];
            payload["orig_lat"] = data["geometry"]["coordinates"][1];

            console.log("Selected start: ");
            console.log(payload);
        }
    );
}

function remove() {
    var last_chq_no = $("#total_chq").val();
    if (last_chq_no > 1) {
        $("#intermediate_point_" + last_chq_no).remove();
        $("#total_chq").val(last_chq_no - 1);
    }
}
