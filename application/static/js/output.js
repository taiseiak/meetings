function getMemos() {
    $.getJSON("/_get_memos", function(data) {
        var memos = data.results.memos
        if (memos != "none") {
            var memoString = "";
            for (i = 0; i < memos.length; i++) {
                var memo = memos[i];
                memoString += "<div class='well' id='" + memo._id + "'><h4>" + memo.human_date +
                "</h4><p>" + memo.memo + "</p><button type='button' class='btn btn-danger delete'>Delete</button></div>";
            };
            $('#memos').html(memoString);
            $('.delete').on('click', function(event) {
                $.get("/_delete_memo", {id: $(this).parent().attr('id')}, function() {
                    getMemos();
                });
            });
        } else {
            $('#memos').html("<div class='well'><h4>No Memos</h4></div>");
        }
    });
}

getMemos();

function clearInputs() {
    var today = moment().format('YYYY-MM-DD').toString();
    $('#date').val(today);
    $('#memo').val('');
}

clearInputs();

$('#save').on('click', function(event) {
    var rawDate = $('#date').val();
    var memo = $('#memo').val();
    var memo = memo.replace(/(\n)+/g, '<br />');
    if (rawDate && memo) {
        var date = moment(rawDate).toISOString();
        $.post("/_post_memo", {date: date, memo: memo}, function() {
            clearInputs();
            getMemos();
        });
    }
});

$('#clear').on('click', function(even) {
    clearInputs();
});