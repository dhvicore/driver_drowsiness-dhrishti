import time
import numpy as np
from collections import deque


class TemporalEngine:

    def __init__(self):

        # ====================================================
        # THRESHOLDS
        # ====================================================

        # Based on your webcam tests:
        # open eyes ~0.30-0.40
        # closed eyes ~0.15
        self.EYE_CLOSE_THRESHOLD = 0.23
        self.EYE_OPEN_THRESHOLD = 0.27

        # Yawn MAR
        self.YAWN_START_THRESHOLD = 0.42
        self.YAWN_STOP_THRESHOLD = 0.28

        # Minimum duration before mouth opening counts as yawn
        self.YAWN_CONFIRM_SECONDS = 0.65

        # Blink timing
        self.BLINK_MIN_SECONDS = 0.08
        self.BLINK_MAX_SECONDS = 0.65

        # Long eye closure
        self.LONG_CLOSURE_SECONDS = 0.8

        # Memory windows
        self.PERCLOS_WINDOW_SECONDS = 30.0
        self.YAWN_MEMORY_SECONDS = 45.0
        self.CLOSURE_MEMORY_SECONDS = 30.0

        # ====================================================
        # SMOOTHING
        # ====================================================

        self.ear_history = deque(maxlen=7)
        self.mar_history = deque(maxlen=7)

        # Stores (timestamp, closed?)
        self.perclos_history = deque()

        # Event timestamps
        self.yawn_events = deque()
        self.long_closure_events = deque()

        # ====================================================
        # EYE STATE
        # ====================================================

        self.eye_state = "OPEN"

        self.eye_closed_start = None
        self.current_closure_registered = False

        self.blink_count = 0

        # ====================================================
        # YAWN STATE
        # ====================================================

        self.yawn_state = False
        self.yawn_candidate_start = None
        self.yawn_count = 0

        # ====================================================
        # DISPLAY SCORE
        # ====================================================

        self.display_score = 0.0


    # ========================================================
    # REMOVE OLD EVENTS
    # ========================================================

    def _clean_old_events(self, now):

        # ---------------- PERCLOS ----------------

        while (
            self.perclos_history
            and
            now - self.perclos_history[0][0]
            > self.PERCLOS_WINDOW_SECONDS
        ):
            self.perclos_history.popleft()

        # ---------------- YAWNS ----------------

        while (
            self.yawn_events
            and
            now - self.yawn_events[0]
            > self.YAWN_MEMORY_SECONDS
        ):
            self.yawn_events.popleft()

        # ---------------- LONG CLOSURES ----------------

        while (
            self.long_closure_events
            and
            now - self.long_closure_events[0]
            > self.CLOSURE_MEMORY_SECONDS
        ):
            self.long_closure_events.popleft()


    # ========================================================
    # MAIN UPDATE
    # ========================================================

    def update(self, raw_ear, raw_mar):

        now = time.time()

        # ====================================================
        # SMOOTH EAR + MAR
        # ====================================================

        self.ear_history.append(float(raw_ear))
        self.mar_history.append(float(raw_mar))

        ear = float(
            np.median(self.ear_history)
        )

        mar = float(
            np.median(self.mar_history)
        )


        # ====================================================
        # EYE STATE WITH HYSTERESIS
        # ====================================================

        previous_eye_state = self.eye_state

        if self.eye_state == "OPEN":

            if ear <= self.EYE_CLOSE_THRESHOLD:
                self.eye_state = "CLOSED"

        else:

            if ear >= self.EYE_OPEN_THRESHOLD:
                self.eye_state = "OPEN"


        # ====================================================
        # EYE CLOSED
        # ====================================================

        if self.eye_state == "CLOSED":

            if self.eye_closed_start is None:

                self.eye_closed_start = now
                self.current_closure_registered = False

            closed_duration = (
                now - self.eye_closed_start
            )

            self.perclos_history.append(
                (now, 1)
            )

            # Register long closure ONCE
            if (
                closed_duration
                >= self.LONG_CLOSURE_SECONDS
                and
                not self.current_closure_registered
            ):

                self.long_closure_events.append(now)

                self.current_closure_registered = True


        # ====================================================
        # EYE OPEN
        # ====================================================

        else:

            closed_duration = 0.0

            self.perclos_history.append(
                (now, 0)
            )

            # Closed -> Open transition
            if (
                previous_eye_state == "CLOSED"
                and
                self.eye_closed_start is not None
            ):

                closure_length = (
                    now - self.eye_closed_start
                )

                # Only normal short closure = blink
                if (
                    self.BLINK_MIN_SECONDS
                    <= closure_length
                    <= self.BLINK_MAX_SECONDS
                ):

                    self.blink_count += 1

            self.eye_closed_start = None
            self.current_closure_registered = False


        # ====================================================
        # YAWN DETECTION WITH HYSTERESIS
        # ====================================================

        if not self.yawn_state:

            if mar >= self.YAWN_START_THRESHOLD:

                if self.yawn_candidate_start is None:
                    self.yawn_candidate_start = now

                candidate_duration = (
                    now - self.yawn_candidate_start
                )

                if (
                    candidate_duration
                    >= self.YAWN_CONFIRM_SECONDS
                ):

                    self.yawn_state = True

                    self.yawn_count += 1

                    self.yawn_events.append(now)

                    self.yawn_candidate_start = None

            else:

                self.yawn_candidate_start = None


        else:

            # Need mouth to clearly close before ending yawn
            if mar <= self.YAWN_STOP_THRESHOLD:

                self.yawn_state = False
                self.yawn_candidate_start = None


        # ====================================================
        # CLEAN OLD EVENTS
        # ====================================================

        self._clean_old_events(now)


        # ====================================================
        # PERCLOS
        # ====================================================

        if len(self.perclos_history) > 0:

            closed_samples = sum(
                value
                for _, value
                in self.perclos_history
            )

            perclos = (
                closed_samples
                /
                len(self.perclos_history)
            )

        else:

            perclos = 0.0


        recent_yawns = len(
            self.yawn_events
        )

        recent_long_closures = len(
            self.long_closure_events
        )


        # ====================================================
        # DROWSINESS EVIDENCE SCORE
        # ====================================================

        target_score = 0


        # ----------------------------------------------------
        # CURRENT EYE CLOSURE
        # ----------------------------------------------------

        if closed_duration >= 3.0:

            target_score += 85

        elif closed_duration >= 2.0:

            target_score += 65

        elif closed_duration >= 1.5:

            target_score += 45

        elif closed_duration >= 0.8:

            target_score += 20


        # ----------------------------------------------------
        # PERCLOS
        # ----------------------------------------------------

        if perclos >= 0.50:

            target_score += 30

        elif perclos >= 0.40:

            target_score += 25

        elif perclos >= 0.30:

            target_score += 18

        elif perclos >= 0.20:

            target_score += 10


        # ----------------------------------------------------
        # RECENT YAWNS
        # ----------------------------------------------------

        if recent_yawns >= 3:

            target_score += 30

        elif recent_yawns == 2:

            target_score += 20

        elif recent_yawns == 1:

            target_score += 10


        # Active yawn
        if self.yawn_state:

            target_score += 5


        # ----------------------------------------------------
        # RECENT LONG CLOSURES
        # ----------------------------------------------------

        if recent_long_closures >= 4:

            target_score += 25

        elif recent_long_closures >= 2:

            target_score += 18

        elif recent_long_closures == 1:

            target_score += 8


        # ----------------------------------------------------
        # MULTI-CUE BONUS
        # ----------------------------------------------------

        current_eye_warning = (
            closed_duration >= 0.8
        )

        high_perclos = (
            perclos >= 0.35
        )

        frequent_yawning = (
            recent_yawns >= 2
        )


        if (
            current_eye_warning
            and
            frequent_yawning
        ):

            target_score += 10


        elif (
            current_eye_warning
            and
            high_perclos
        ):

            target_score += 10


        target_score = min(
            target_score,
            100
        )


        # ====================================================
        # SMOOTH DROWSINESS SCORE
        # ====================================================

        # Danger should rise quickly.
        if target_score > self.display_score:

            rise_rate = 0.20

            self.display_score += (
                target_score
                -
                self.display_score
            ) * rise_rate


        # Recovery should happen gradually.
        else:

            fall_rate = 0.08

            self.display_score += (
                target_score
                -
                self.display_score
            ) * fall_rate


        # ====================================================
        # EXTRA RECOVERY
        # ====================================================

        clearly_recovered = (

            self.eye_state == "OPEN"

            and

            not self.yawn_state

            and

            closed_duration == 0.0
        )


        if clearly_recovered:

            self.display_score -= 0.12


        self.display_score = max(
            0.0,
            min(
                self.display_score,
                100.0
            )
        )


        score = int(
            round(
                self.display_score
            )
        )


        # ====================================================
        # FINAL STATUS
        # ====================================================

        # ----------------------------------------------------
        # CRITICAL
        #
        # Requires CURRENT severe evidence.
        # ----------------------------------------------------

        if closed_duration >= 3.0:

            status = "CRITICAL"


        elif (
            closed_duration >= 2.0
            and
            recent_yawns >= 2
        ):

            status = "CRITICAL"


        # ----------------------------------------------------
        # DROWSY
        # ----------------------------------------------------

        elif closed_duration >= 1.5:

            status = "DROWSY"


        elif (
            perclos >= 0.45
            and
            recent_long_closures >= 2
        ):

            status = "DROWSY"


        elif (
            score >= 55
            and
            (
                perclos >= 0.35
                or
                closed_duration >= 0.8
            )
        ):

            status = "DROWSY"


        # ----------------------------------------------------
        # FATIGUED
        # ----------------------------------------------------

        elif recent_yawns >= 2:

            status = "FATIGUED"


        elif score >= 30:

            status = "FATIGUED"


        # ----------------------------------------------------
        # ALERT
        # ----------------------------------------------------

        else:

            status = "ALERT"


        # ====================================================
        # RETURN EVERYTHING MAIN.PY EXPECTS
        # ====================================================

        return {

            "eye_state":
                self.eye_state,

            "ear":
                ear,

            "mar":
                mar,

            "closed_duration":
                closed_duration,

            "blink_count":
                self.blink_count,

            "perclos":
                perclos,

            "yawn":
                self.yawn_state,

            "yawn_count":
                self.yawn_count,

            "recent_yawns":
                recent_yawns,

            "recent_long_closures":
                recent_long_closures,

            "target_score":
                target_score,

            "score":
                score,

            "status":
                status
        }