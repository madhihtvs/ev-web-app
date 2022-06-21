import json

from flask import Flask, redirect, render_template, request, url_for

import preprocessing

app = Flask(__name__)

session = {}


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
                last_leg

        ) = preprocessing.process_inputs(
            start_point=start_point,
            end_point=end_point,
            range_start=range_start,
            range_arrival=range_arrival,
            start_time=start_time,
        )
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
    )


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
