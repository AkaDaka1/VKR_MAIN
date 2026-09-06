package com.vkr.theaterclient.core.model

import com.squareup.moshi.Json

data class AuthToken(
    val accessToken: String,
    val tokenType: String,
)

data class CustomerMe(
    val email: String,
    val phone: String?,
    @Json(name = "is_active")
    val isActive: Boolean,
)

data class Theater(
    @Json(name = "theater_id")
    val theaterId: Int,
    val name: String?,
    val location: String?,
)

data class Show(
    @Json(name = "show_id")
    val showId: Int,
    val title: String?,
    @Json(name = "show_date")
    val showDate: String?,
)

data class Seat(
    @Json(name = "ticket_id")
    val ticketId: Int,
    @Json(name = "seat_number")
    val seatNumber: String?,
    val status: String?,
    val price: Double?,
)

data class ReservationRequest(
    @Json(name = "show_id")
    val showId: Int,
    @Json(name = "seat_number")
    val seatNumber: String,
)
