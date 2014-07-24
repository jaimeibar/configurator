/**
 * Created by jim on 12/03/14.
*/

function get_selected(sname) {
    $.ajax({
        data: {
            name: sname
        },
        url: "/index/",
        dataType: "json",
        success: function(data) {
            if ($("#table_hosts").length != 0) {
                $("#div_hostlist").empty();
            }
            var tcontent = "<table id='table_hosts' class='table table-bordered table-hover'>" +
                "<thead><tr><th><input id='all_hosts' type='checkbox' name='all_hosts' onchange='check_all()'></th>" +
                "<th>Hostname</th><th>IP</th></tr></thead><tbody></tbody></table>";
            $("#div_hostlist").append($(tcontent));
            /*
            $.each(data, function(i, item) {
                // console.log("hostname: " + data[i].fields.hostname);
                // console.log("hostname: " + item.fields.hostname);
            });
            */
            $.each(data, function(i, item) {
                var hostname = item.fields.hostname;
                var ip = item.fields.ip;
                var content = "<tr><td><input type='checkbox' name='hosts' onchange='enable_go_button()' value=" + hostname + "></td>"
                content += "<td>" + hostname + "</td>"
                content += "<td>" + ip + "</td></tr>";
                $("#table_hosts").find("tbody:last").append($(content));
            });
        }
    });
    $( "#button_clear").prop("disabled", false);
}

function get_host() {
    var selected_hosts = [];
    var checked_hosts = $( "input:checkbox[name=hosts]:checked" );
    checked_hosts.each(function() {
        selected_hosts.push($(this).val());
    })
    alert(selected_hosts);
}

function check_all() {
    var c = $("input:checkbox[name=all_hosts]")[0].checked;
    $("input:checkbox[name=hosts]").prop('checked', c);
    enable_go_button();
}

function clear_page() {
    $( "#div_hostlist" ).empty();
    $( "#button_clear").prop("disabled", true);
    enable_go_button();
}

function enable_go_button() {
    var isdisabled = $( "#button_go").prop("disabled");
    if ($( "input:checkbox[name=hosts]:checked").length > 0 || isdisabled == true ) {
        $( "#button_go").prop("disabled", false);
        $( "#id-select-commands").prop("disabled", false);
    } else {
        $( "#button_go").prop("disabled", true);
        $( "#id-select-commands").prop("disabled", true);
    }
}