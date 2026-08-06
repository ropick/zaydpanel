import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { z } from 'zod';

const orderSchema = z.object({
  name: z.string().min(2, 'Nama minimal 2 karakter'),
  email: z.string().email('Email tidak valid'),
  phone: z.string().min(8, 'Nomor telepon minimal 8 digit'),
  package: z.enum(['Starter', 'Business', 'Premium']),
  domain: z.string().optional(),
  message: z.string().optional(),
});

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const validated = orderSchema.parse(body);

    const order = await db.hostingOrder.create({
      data: {
        name: validated.name,
        email: validated.email,
        phone: validated.phone,
        package: validated.package,
        domain: validated.domain || null,
        message: validated.message || null,
      },
    });

    return NextResponse.json(
      {
        success: true,
        message: 'Pesanan berhasil dibuat! Tim kami akan menghubungi Anda dalam 1x24 jam.',
        orderId: order.id,
      },
      { status: 201 }
    );
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { success: false, message: error.errors[0].message },
        { status: 400 }
      );
    }
    console.error('Order error:', error);
    return NextResponse.json(
      { success: false, message: 'Terjadi kesalahan server. Silakan coba lagi.' },
      { status: 500 }
    );
  }
}
