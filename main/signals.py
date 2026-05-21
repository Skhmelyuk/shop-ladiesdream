from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from .models import Product, ProductImage, Category

def delete_file_and_variants(field_file):
    if not field_file:
        return
    import os
    try:
        path = field_file.path
        if os.path.exists(path):
            os.remove(path)
            
        dir_name = os.path.dirname(path)
        base_name = os.path.splitext(os.path.basename(path))[0]
        
        # Variants suffix
        variants = [
            f"{base_name}.webp",
            f"{base_name}_thumbnail.webp",
            f"{base_name}_catalog.webp",
            f"{base_name}_card.webp"
        ]
        
        for variant in variants:
            variant_path = os.path.join(dir_name, variant)
            if os.path.exists(variant_path) and variant_path != path:
                os.remove(variant_path)
    except Exception:
        pass

@receiver(post_save, sender=Product)
def product_post_save(sender, instance, created, **kwargs):
    if instance.image:
        from main.tasks import process_product_image
        process_product_image.delay('Product', instance.id)

@receiver(post_save, sender=ProductImage)
def product_image_post_save(sender, instance, created, **kwargs):
    if instance.image:
        from main.tasks import process_product_image
        process_product_image.delay('ProductImage', instance.id)

# --- DELETE SIGNALS ---
@receiver(post_delete, sender=Category)
def category_post_delete(sender, instance, **kwargs):
    if instance.image:
        delete_file_and_variants(instance.image)

@receiver(post_delete, sender=Product)
def product_post_delete(sender, instance, **kwargs):
    if instance.image:
        delete_file_and_variants(instance.image)

@receiver(post_delete, sender=ProductImage)
def product_image_post_delete(sender, instance, **kwargs):
    if instance.image:
        delete_file_and_variants(instance.image)

# --- PRE-SAVE CHANGE SIGNALS ---
@receiver(pre_save, sender=Category)
def category_pre_save(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old_instance = Category.objects.get(pk=instance.pk)
        if old_instance.image and old_instance.image != instance.image:
            delete_file_and_variants(old_instance.image)
    except Category.DoesNotExist:
        pass

@receiver(pre_save, sender=Product)
def product_pre_save(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old_instance = Product.objects.get(pk=instance.pk)
        if old_instance.image and old_instance.image != instance.image:
            delete_file_and_variants(old_instance.image)
    except Product.DoesNotExist:
        pass

@receiver(pre_save, sender=ProductImage)
def product_image_pre_save(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old_instance = ProductImage.objects.get(pk=instance.pk)
        if old_instance.image and old_instance.image != instance.image:
            delete_file_and_variants(old_instance.image)
    except ProductImage.DoesNotExist:
        pass
