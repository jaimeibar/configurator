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
            var divhostlist = $("#div_hostlist");
            if ($("#table_hosts").length != 0) {
                divhostlist.empty();
            }
            var tcontent = "<table id='table_hosts' class='table table-bordered table-hover'>" +
                "<thead><tr><th><input id='all_hosts' type='checkbox' name='all_hosts' onchange='check_all()'></th>" +
                "<th>Hostname</th><th>IP</th><th>Status</th></tr></thead><tbody></tbody></table>";
            divhostlist.append($(tcontent));
            $.each(data, function(i, item) {
                var hostname = item.fields.hostname;
                var shorthostname = hostname.split(".", 1);
                var ip = item.fields.ip;
                var content = "<tr id=" + shorthostname + "><td><input type='checkbox' name='hosts' onchange='checked_host()' value=" + shorthostname + "></td>";
                content += "<td id=" + shorthostname + "h>" + shorthostname + "</td>";
                content += "<td id=" + shorthostname + "i>" + ip + "</td>";
                content += "<td id=" + shorthostname + "s></td></tr>";
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
        traditional: true,
        success: function(data) {
            if ($.isEmptyObject(data)) {
                console.log('No data received');
            } else {
                $.each(data, function(key, value) {
                    var status = value.power;
                    var tdstatus = $("td[id*='" + key + "s']");
                    tdstatus.text(status);
                    if (status == 'on') {
                        tdstatus.addClass("onstatus");
                    } else {
                        tdstatus.addClass("offstatus");
                    }
                })
            }
        },
        error: function(data) {
            console.log("Error");
        }
    });
}

function check_all() {
    var selector = $("#id-select-commands");
    var buttongo = $("#button_go");
    if ($("input:checkbox[name=hosts]:checked").length == 0) {
        $("input:checkbox[name=hosts]").prop('checked', true);
        buttongo.prop("disabled", false);
        buttongo.text("Go (36)");
        selector.prop("disabled", false);
        selector.find("option[id=status]").prop("selected", true);
    } else {
        $("input:checkbox[name=hosts]").prop('checked', false);
        buttongo.text("Go (0)");
        buttongo.prop("disabled", true);
        selector.prop("disabled", true);
        selector.find("option[id=empty]").prop("selected", true);
    }
}

function clear_page() {
    $("#div_hostlist").empty();
    manage_go_button();
    manage_clear_button();
}

function manage_go_button() {
    var buttongo = $("#button_go");
    var isdisabled = buttongo.prop("disabled");
    if (isdisabled == true) {
        if ($("input:checkbox[name=hosts]:checked").length == 0) {
            buttongo.prop("disabled", true);
        } else {
            buttongo.prop("disabled", false);
        }
    } else {
        buttongo.prop("disabled", true);
    }
}

function manage_clear_button() {
    var clearbtn = $("#button_clear");
    var isdisabled = clearbtn.prop("disabled");
    if (isdisabled == true) {
        clearbtn.prop("disabled", false);
    } else {
        clearbtn.prop("disabled", true);
    }
}

function checked_host() {
    var selector = $("#id-select-commands");
    var buttongo = $("#button_go");
    var nhosts = $("input:checkbox[name=hosts]:checked").length;
    if (nhosts > 0) {
        buttongo.prop("disabled", false);
        buttongo.text("Go (" + nhosts + ")");
        selector.prop("disabled", false);
        selector.find("option[id=status]").prop("selected", true);
        if (nhosts == 36) {
            $("#all_hosts").prop("checked", true);
        } else {
            $("#all_hosts").prop("checked", false);
        }
    } else {
        buttongo.text("Go (" + nhosts + ")");
        buttongo.prop("disabled", true);
        selector.prop("disabled", true);
        selector.find("option[id=empty]").prop("selected", true);
    }
}