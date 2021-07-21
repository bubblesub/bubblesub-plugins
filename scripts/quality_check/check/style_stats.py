from collections import defaultdict

from .base import BaseCheck


class CheckStyleStats(BaseCheck):
    def run(self) -> None:
        self.api.log.info("Styles summary:")
        styles = defaultdict(int)

        for line in self.api.subs.events:
            styles[line.style] += 1

        for style, occurrences in sorted(
            styles.items(), key=lambda kv: -kv[1]
        ):
            self.api.log.info(f"– {occurrences} time(s): {style}")
