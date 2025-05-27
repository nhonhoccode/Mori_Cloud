import os
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from morisite.models import Trash, Photo

class Command(BaseCommand):
    help = "Tự động xóa ảnh trong Trash sau 30 ngày"
    def handle(self, *args, **kwargs):
        cutoff = timezone.now() - timedelta(days=30)
        old_trashes = Trash.objects.filter(deleted_at__lt=cutoff)

        total = old_trashes.count()
        if total == 0:
            self.stdout.write("Không có ảnh nào cần xóa.")
            return

        for trash in old_trashes:
            photo = trash.photo
            path = photo.photo.path
            if os.path.exists(path):
                os.remove(path)
                self.stdout.write(f"Đã xóa file: {path}")
            else:
                self.stdout.write(f"File không tồn tại: {path}")
            trash.delete()
            photo.delete()
        self.stdout.write(self.style.SUCCESS(f"Đã xóa {total} ảnh khỏi Trash sau 30 ngày."))
