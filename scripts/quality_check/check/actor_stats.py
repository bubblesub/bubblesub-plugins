from collections import defaultdict

from .base import BaseCheck


class CheckActorStats(BaseCheck):
    async def run(self) -> None:
        self.api.log.info("Actors summary:")
        actors = defaultdict(int)

        for event in self.api.subs.events:
            actors[event.actor] += 1

        for actor, occurrences in sorted(
            actors.items(), key=lambda kv: -kv[1]
        ):
            self.api.log.info(f"– {occurrences} time(s): {actor}")
