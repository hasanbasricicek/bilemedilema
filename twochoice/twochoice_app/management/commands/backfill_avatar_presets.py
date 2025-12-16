from django.core.management.base import BaseCommand

from twochoice_app.avatar import get_preset_config, sanitize_avatar_config
from twochoice_app.models import UserProfile


class Command(BaseCommand):
    help = (
        "Backfill avatar presets into avatar_config (single source of truth). "
        "Converts avatar_mode='preset' rows to avatar_mode='custom', clears avatar_preset, "
        "and writes resolved avatar_config."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Do not write changes, only print what would change.',
        )

    def handle(self, *args, **options):
        dry_run = bool(options.get('dry_run'))

        qs = UserProfile.objects.filter(avatar_mode='preset')
        total = qs.count()
        updated = 0
        skipped = 0

        self.stdout.write(f'Found {total} profiles with avatar_mode=preset')

        for p in qs.iterator():
            preset_key = (p.avatar_preset or '').strip()
            preset_cfg = get_preset_config(preset_key) if preset_key else None

            if not preset_cfg:
                skipped += 1
                continue

            new_cfg = sanitize_avatar_config(preset_cfg)
            if p.avatar_mode == 'custom' and p.avatar_preset == '' and (p.avatar_config or {}) == new_cfg:
                skipped += 1
                continue

            if dry_run:
                self.stdout.write(
                    f'[DRY RUN] would update profile_id={p.id} user_id={p.user_id} preset={preset_key}'
                )
                updated += 1
                continue

            p.avatar_mode = 'custom'
            p.avatar_preset = ''
            p.avatar_config = new_cfg
            p.save(update_fields=['avatar_mode', 'avatar_preset', 'avatar_config'])
            updated += 1

        self.stdout.write(self.style.SUCCESS(f'Updated: {updated}, skipped: {skipped}, total: {total}'))
        if dry_run:
            self.stdout.write(self.style.WARNING('Dry run enabled; no changes were written.'))
