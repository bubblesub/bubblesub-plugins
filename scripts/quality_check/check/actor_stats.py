from collections import defaultdict

from .base import BaseCheck


class CheckActorStats(BaseCheck):
    def run(self) -> None:
        self.api.log.info("Actors summary:")
        actors = defaultdict(int)

        for line in self.api.subs.events:
            actors[line.actor] += 1

        for actor, occurrences in sorted(
            actors.items(), key=lambda kv: -kv[1]
        ):
            self.api.log.info(f"– {occurrences} time(s): {actor}")
