package com.vkr.theaterclient.core.network

import com.squareup.moshi.Json
import com.vkr.theaterclient.core.model.CustomerMe
import com.vkr.theaterclient.core.model.ReservationRequest
import com.vkr.theaterclient.core.model.Seat
import com.vkr.theaterclient.core.model.Show
import com.vkr.theaterclient.core.model.Theater
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

data class RegisterRequest(
    val email: String,
    val phone: String?,
    val password: String,
)

data class LoginRequest(
    val email: String,
    val password: String,
)

data class TokenResponse(
    @Json(name = "access_token") val accessToken: String,
    @Json(name = "token_type") val tokenType: String,
)

interface PublicApi {
    @POST("public/v1/auth/register")
    suspend fun register(@Body request: RegisterRequest): CustomerMe

    @POST("public/v1/auth/login")
    suspend fun login(@Body request: LoginRequest): TokenResponse

    @GET("public/v1/me")
    suspend fun me(): CustomerMe

    @GET("public/v1/theaters")
    suspend fun theaters(): List<Theater>

    @GET("public/v1/theaters/{theaterId}/shows")
    suspend fun shows(
        @Path("theaterId") theaterId: Int,
        @Query("show_date") showDate: String? = null,
    ): List<Show>

    @GET("public/v1/shows/{showId}/seats")
    suspend fun seats(@Path("showId") showId: Int): List<Seat>

    @POST("public/v1/reservations")
    suspend fun reserve(@Body request: ReservationRequest): Seat

    @GET("public/v1/reservations/my")
    suspend fun myReservations(): List<Seat>
}
