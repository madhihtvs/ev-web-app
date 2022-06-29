import json

from flask import Flask, redirect, render_template, request, url_for

import preprocessing

app = Flask(__name__)

session = {}

session_no_night = {}

session_own_rest = {}


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        (
            start_point,
            end_point,
            range_start,
            range_arrival,
            start_time,
        ) = preprocessing.collect_user_inputs(request.values)

        (
                marker_lst,
                markers,
                mid_lat,
                mid_lon,
                point_list,
                distance,
                time,
                initial_soc,
                final_threshold,
                start_time,
                lst,
                res,
                last_leg,
                night_travel,
                time_end

        ) = preprocessing.process_inputs(
            start_point=start_point,
            end_point=end_point,
            range_start=range_start,
            range_arrival=range_arrival,
            start_time=start_time,
        )

        session["start-point"] = start_point
        session["end-point"] = end_point
        session["range-start"] = range_start
        session["range-arrival"] = range_arrival
        session["start-time"] = start_time

        session["marker_lst"] = json.dumps(marker_lst)
        session["markers"] = markers
        session["mid_lat"] = mid_lat
        session["mid_lon"] = mid_lon
        session["pointList"] = json.dumps(point_list)
        session["last_leg"] = json.dumps(last_leg)
        session["distance"] = distance
        session["time"] = time
        session["initial_soc"] = initial_soc
        session["final_threshold"] = final_threshold
        session["trip_start_at"] = json.dumps(start_time)
        session["details"] = json.dumps(lst)
        session["lst"] = json.dumps(res)
        session["night_travel"] = json.dumps(night_travel)
        session["time_end"] = time_end
        


        return redirect(url_for("results"))
    return render_template("index.html")


@app.route("/results", methods=["GET", "POST"])
def results():
    return render_template(
        "results.html",
        marker_lst = session.get("marker_lst"),
        markers=session.get("markers"),
        lat=session.get("mid_lat"),
        lon=session.get("mid_lon"),
        pointList=session.get("pointList"),
        last_leg=session.get("last_leg"),
        distance=session.get("distance"),
        time=session.get("time"),
        intial_soc=session.get("initial_soc"),
        final_threshold=session.get("final_threshold"),
        trip_start_at=session.get("trip_start_at"),
        lst=session.get("lst"),
        details=session.get("details"),
        night_travel = session.get("night_travel"),
        time_end = session.get("time_end")
    )


@app.route('/ownrest', methods=['GET','POST'])
def ownrest():
    rest_point = str(request.values.get('rest'))
    start_point = session.get("start-point")
    end_point = session.get("end-point")
    total_distance = session.get("distance")
    range_start = session.get("range-start")
    range_arrival = session.get("range-arrival")
    start_time = session.get("start-time")

    (
                marker_lst,
                markers,
                mid_lat,
                mid_lon,
                point_list,
                distance,
                time,
                initial_soc,
                final_threshold,
                start_time,
                lst,
                res,
                last_leg,
                night_travel,
                time_end,
                last_leg2,
                rest_charge_last_leg

    ) = preprocessing.process_inputs_own_rest(
            start_point=start_point,
            rest_point=rest_point,
            end_point=end_point,
            range_start=range_start,
            range_arrival=range_arrival,
            start_time=start_time,
            total_distance = total_distance
    )

    session_own_rest["marker_lst"] = json.dumps(marker_lst)
    session_own_rest["markers"] = markers
    session_own_rest["mid_lat"] = mid_lat
    session_own_rest["mid_lon"] = mid_lon
    session_own_rest["pointList"] = json.dumps(point_list)
    session_own_rest["last_leg"] = json.dumps(last_leg)
    session_own_rest["distance"] = distance
    session_own_rest["time"] = time
    session_own_rest["initial_soc"] = initial_soc
    session_own_rest["final_threshold"] = final_threshold
    session_own_rest["trip_start_at"] = json.dumps(start_time)
    session_own_rest["details"] = json.dumps(lst)
    session_own_rest["lst"] = json.dumps(res)
    session_own_rest["night_travel"] = json.dumps(night_travel)
    session_own_rest["time_end"] = time_end
    session_own_rest["last_leg2"] = json.dumps(last_leg2)
    session_own_rest["rest_charge_last_leg"] = json.dumps(rest_charge_last_leg)


    return render_template("ownrest.html",
            marker_lst = session_own_rest.get("marker_lst"),
            markers=session_own_rest.get("markers"),
            lat=session_own_rest.get("mid_lat"),
            lon=session_own_rest.get("mid_lon"),
            pointList=session_own_rest.get("pointList"),
            last_leg=session_own_rest.get("last_leg"),
            distance=session_own_rest.get("distance"),
            time=session_own_rest.get("time"),
            intial_soc=session_own_rest.get("initial_soc"),
            final_threshold=session_own_rest.get("final_threshold"),
            trip_start_at=session_own_rest.get("trip_start_at"),
            lst=session_own_rest.get("lst"),
            details=session_own_rest.get("details"),
            night_travel = session_own_rest.get("night_travel"),
            time_end = session_own_rest.get("time_end"),
            last_leg2 = session_own_rest.get("last_leg2"),
            rest_charge_last_leg = session_own_rest.get("rest_charge_last_leg"),
            )

@app.route('/userchoice', methods=['GET','POST'])
def userchoice():
    
    clicked=request.values.get('clicked')
    values = {str(i): i for i in range(1,4)}
    clicked = values[clicked]

    if clicked == 3:
        session["night_travel"] = 'false'
        return render_template(
        "option3.html",
        marker_lst = session.get("marker_lst"),
        markers=session.get("markers"),
        lat=session.get("mid_lat"),
        lon=session.get("mid_lon"),
        pointList=session.get("pointList"),
        last_leg=session.get("last_leg"),
        distance=session.get("distance"),
        time=session.get("time"),
        intial_soc=session.get("initial_soc"),
        final_threshold=session.get("final_threshold"),
        trip_start_at=session.get("trip_start_at"),
        lst=session.get("lst"),
        details=session.get("details"),
        night_travel = session.get("night_travel"),
        time_end = session.get("time_end")
    )

    elif clicked == 2:
        return render_template("option2.html")

    elif clicked == 1:
        start_point = session.get("start-point")
        end_point = session.get("end-point")
        range_start = session.get("range-start")
        range_arrival = session.get("range-arrival")
        start_time = session.get("start-time")

        (
                marker_lst,
                markers,
                mid_lat,
                mid_lon,
                point_list,
                distance,
                time,
                initial_soc,
                final_threshold,
                start_time,
                lst,
                res,
                last_leg,
                night_travel,
                time_end

        ) = preprocessing.process_inputs_nonight(
            start_point=start_point,
            end_point=end_point,
            range_start=range_start,
            range_arrival=range_arrival,
            start_time=start_time,
        )
        session_no_night["marker_lst"] = json.dumps(marker_lst)
        session_no_night["markers"] = markers
        session_no_night["mid_lat"] = mid_lat
        session_no_night["mid_lon"] = mid_lon
        session_no_night["pointList"] = json.dumps(point_list)
        session_no_night["last_leg"] = json.dumps(last_leg)
        session_no_night["distance"] = distance
        session_no_night["time"] = time
        session_no_night["initial_soc"] = initial_soc
        session_no_night["final_threshold"] = final_threshold
        session_no_night["trip_start_at"] = json.dumps(start_time)
        session_no_night["details"] = json.dumps(lst)
        session_no_night["lst"] = json.dumps(res)
        session_no_night["night_travel"] = json.dumps(night_travel)
        session_no_night["time_end"] = time_end

        return render_template(
        "option1.html",
        marker_lst = session_no_night.get("marker_lst"),
        markers=session_no_night.get("markers"),
        lat=session_no_night.get("mid_lat"),
        lon=session_no_night.get("mid_lon"),
        pointList=session_no_night.get("pointList"),
        last_leg=session_no_night.get("last_leg"),
        distance=session_no_night.get("distance"),
        time=session_no_night.get("time"),
        intial_soc=session_no_night.get("initial_soc"),
        final_threshold=session_no_night.get("final_threshold"),
        trip_start_at=session_no_night.get("trip_start_at"),
        lst=session_no_night.get("lst"),
        details=session_no_night.get("details"),
        night_travel = session_no_night.get("night_travel"),
        time_end = session_no_night.get("time_end")
    )
        


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
