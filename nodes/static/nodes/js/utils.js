/**
 * Created by jim on 12/03/14.
*/

$(document).ready(function() {
    interval = null;
    bifibutton = $("#Bifi");
    cienciasbutton = $("#Ciencias");
    epshbutton = $("#EPSH");
    euptbutton = $("#EUPT");
    allbutton = $("#all");
    clearbutton = $("#clear");
    commands = $("#commands");
    gobutton = $("#go");
    stopbutton = $("#stop");
});

function get_selected(sname) {
    $.ajax({
        data: {
            name: sname
        },
        url: "/index",
        dataType: "json",
        success: function(data) {
            manage_clear_button(false);
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
    var command = commands.val();
    manage_all_buttons(true);
    $("body").css("cursor", "progress");
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
                interval = setInterval(check_task_status, 3000);
            } else {
                stopbutton.prop("disabled", true);
                $("body").css("cursor", "default");
                get_task_result(data);
                manage_all_buttons(false);
            }
        },
        error: function(data) {
            console.log("Error");
        },
        beforeSend: function() {
            stopbutton.prop("disabled", false);
        }
    });
}

function check_all() {
    var hosts = $("input:checkbox[name=hosts]");
    var numberofhosts = hosts.length;
    var isanyselected = $("input:checkbox[name=hosts]:checked").length;
    if (isanyselected == 0) {
        hosts.prop("checked", true);
        gobutton.prop("disabled", false);
        gobutton.tex("Go (" + numberofhosts + ")");
        commands.prop("disabled", false);
        commands.find("option[id=empty]").remove();
        commands.find("option[id=status]").prop("selected", true);
    } else if (isanyselected == 36 || isanyselected == 144) {
        hosts.prop("checked", false);
        gobutton.prop("disabled", true);
        gobutton.text("Go (0)");
        commands.prop("disabled", true);
        commands.find("option[id=up]").before("<option id=empty selected></option>");
    } else {
        $("input:checkbox[name=hosts]:not(:checked)").prop("checked", true);
        gobutton.text("Go ("+ numberofhosts + ")");
    }
}

function clear_page() {
    $("#div_hostlist").empty();
    manage_go_button();
    manage_clear_button(true);
    stopbutton.prop("disabled", true);
    commands.prop("disabled", true);
    commands.find("option[id=up]").before("<option id=empty selected></option>");
}

function manage_go_button() {
    var isdisabled = gobutton.prop("disabled");
    if (isdisabled) {
        if ($("input:checkbox[name=hosts]:checked").length == 0) {
            gobutton.prop("disabled", true);
        } else {
            gobutton.prop("disabled", false);
        }
    } else {
        var numenabled = $("input:checkbox[name=hosts]:checked").length;
        gobutton.text("Go (" + numenabled + ")");
        gobutton.prop("disabled", true);
    }
}

function manage_clear_button(state) {
    clearbutton.prop("disabled", state);
}

function checked_host() {
    var nhosts = $("input:checkbox[name=hosts]:checked").length;
    if (nhosts > 0) {
        gobutton.prop("disabled", false);
        gobutton.text("Go (" + nhosts + ")");
        commands.prop("disabled", false);
        commands.find("option[id=empty]").remove();
        commands.find("option[id=status]").prop("selected", true);
        if (nhosts == 36) {
            $("#all_hosts").prop("checked", true);
        } else {
            $("#all_hosts").prop("checked", false);
        }
    } else {
        gobutton.text("Go (" + nhosts + ")");
        gobutton.prop("disabled", true);
        commands.prop("disabled", true);
        commands.find("option[id=up]").before("<option id=empty selected></option>");
    }
}

function stop() {
    $.ajax({
        data: 'cancel',
        type: "GET",
        url: "/index",
        dataType: "json",
        traditional: true,
        success: function(data) {
            clearInterval(interval);
        },
        complete: function() {
            $("body").css("cursor", "default");
            manage_all_buttons(false);
        }
    })
}

function check_task_status() {
    $.ajax({
        data: "status",
        type: "GET",
        url: "/index",
        traditional: true,
        success: function(data) {
            if ($.isEmptyObject(data)) {
                console.log("Task not ready yet");
            } else {
                var checkstatus = $(data).get(0);
                if (checkstatus.status == "complete") {
                    clearInterval(interval);
                    $("body").css("cursor", "default");
                    manage_all_buttons(false);
                    get_task_result(data);
                } else {
                    get_task_result(data);
                }
            }
        },
        error: function() {
            clearInterval(interval);
            manage_all_buttons(false);
        }
    });
}

function get_task_result(data) {
    $.each(data, function(key, value) {
        $.each(value, function (k, v) {
            var status = v.power;
            var tdstatus = $("td[id*='" + k + "s']");
            tdstatus.text(status);
            if (status == "on") {
                tdstatus.addClass("onstatus");
            } else {
                tdstatus.addClass("offstatus");
            }
        })
    })
}

function manage_all_buttons(flag) {
    manage_go_button();
    manage_clear_button();
    bifibutton.prop("disabled", flag);
    cienciasbutton.prop("disabled", flag);
    epshbutton.prop("disabled", flag);
    euptbutton.prop("disabled", flag);
    allbutton.prop("disabled", flag);
    clearbutton.prop("disabled", flag);
    commands.prop("disabled", flag);
}