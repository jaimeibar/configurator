/**
 * Created by jim on 12/03/14.
*/

function get_selected(sname) {
    $.ajax({
        data: {
            name: sname
        },
        url: "/index",
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
                var content = "<tr><td><input type='checkbox' name='hosts' onchange='checked_host()' value=" + hostname + "></td>";
                content += "<td>" + hostname + "</td>";
                content += "<td>" + ip + "</td></tr>";
                $("#table_hosts").find("tbody:last").append($(content));
            });
        }
    });
    $("#button_clear").prop("disabled", false);
}

function get_host() {
    var selected_hosts = [];
    var checked_hosts = $("input:checkbox[name=hosts]:checked");
    checked_hosts.each(function() {
        selected_hosts.push($(this).val());
    });
    return selected_hosts;
}

function get_selected_hosts() {
    $("#button_go").bind("click", function() {
        var allhosts = get_host();
        var command = $("#id-select-commands").val();
        $.ajax({
            type: "GET",
            url: "/index",
            dataType: "json",
            data: {
                selectedhosts: allhosts,
                cmd: command
            },
            success: function(data) {
                console.log(data);
                // var con = "";
                $.each(data, function(i, item) {
                    var con = "<p>" + item.power + "</p>";
                    $("#div-result").append($(con));
                })
            },
            error: function(data) {
                console.log("Error");
            }
        });
    });
}

function check_all() {
    if ($("input:checkbox[name=hosts]:checked").length == 0) {
        $("input:checkbox[name=hosts]").prop('checked', true);
        $("#button_go").prop("disabled", false);
        $("#id-select-commands").prop("disabled", false);
    } else {
        $("input:checkbox[name=hosts]").prop('checked', false);
        $("#button_go").prop("disabled", true);
        $("#id-select-commands").prop("disabled", true);
    }
}

function clear_page() {
    $("#div_hostlist").empty();
    manage_go_button();
    manage_clear_button();
}

function manage_go_button() {
    var isdisabled = $("#button_go").prop("disabled");
    if (isdisabled == true) {
        if ($("input:checkbox[name=hosts]:checked").length == 0) {
            $("#button_go").prop("disabled", true);
        } else {
            $("#button_go").prop("disabled", false);
        }
    } else {
        $("#button_go").prop("disabled", true);
    }
}

function manage_clear_button() {
    var isdisabled = $("#button_clear").prop("disabled");
    if (isdisabled == true) {
        $("#button_clear").prop("disabled", false);
    } else {
        $("#button_clear").prop("disabled", true);
    }
}

function checked_host() {
    var nhosts = $("input:checkbox[name=hosts]:checked").length;
    if (nhosts > 0) {
        $("#button_go").prop("disabled", false);
        $("#id-select-commands").prop("disabled", false);
        if (nhosts == 36) {
            $("#all_hosts").prop("checked", true);
        } else {
            $("#all_hosts").prop("checked", false);
        }
    } else {
        $("#button_go").prop("disabled", true);
        $("#id-select-commands").prop("disabled", true);
    }
}